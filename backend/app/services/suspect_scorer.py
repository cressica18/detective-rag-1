"""Suspect scorer — computes 4 sub-scores and total suspicion score per suspect."""
from app.repositories import sqlite_repo
from app.services import llm_client, retriever
from app.services.prompt_builder import build_motive_score_prompt
from app.utils.logging import get_logger
from app.services.prompt_builder import build_motive_score_prompt, build_batch_motive_prompt

logger = get_logger(__name__)

# Known person roles for the sample case — augmented dynamically
KNOWN_ROLES = {
    "eleanor voss": "victim",
    "marcus bellweather": "suspect",
    "lydia ferro": "suspect",
    "tobias reyes": "suspect",
}

def _normalize_name(raw: str) -> str:
    """Reorder 'Last, First' style names into 'First Last'."""
    name = raw.strip()
    if "," in name:
        parts = [p.strip() for p in name.split(",", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            name = f"{parts[1]} {parts[0]}"
    return name

def _is_victim(key_lower: str) -> bool:
    words = set(key_lower.split())
    return "eleanor" in words and "voss" in words

def _merge_name_variants(people: dict) -> dict:
    """Fold shorter name variants (e.g. just a surname) into the longer name
    that contains all of their words, so 'Bellweather' merges into
    'Marcus Bellweather' instead of appearing as a separate suspect."""
    keys_by_len = sorted(people.keys(), key=len, reverse=True)
    absorbed = set()
    for canonical in keys_by_len:
        if canonical in absorbed:
            continue
        canonical_words = set(canonical.split())
        for other in keys_by_len:
            if other == canonical or other in absorbed:
                continue
            other_words = set(other.split())
            if other_words and other_words.issubset(canonical_words):
                people[canonical]["doc_ids"] |= people[other]["doc_ids"]
                absorbed.add(other)
    return {k: v for k, v in people.items() if k not in absorbed}

from app.services.prompt_builder import build_motive_score_prompt, build_batch_motive_prompt


def score_and_store_suspects(case_id: str):
    """Compute suspect scores for all identified persons and store in SQLite.
    Motive scoring uses a SINGLE batched LLM call across all suspects to minimize quota usage.
    """
    sqlite_repo.delete_suspects_for_case(case_id)

    people_entities = sqlite_repo.get_entities(case_id, entity_type="person")
    contradictions = sqlite_repo.get_contradictions(case_id)
    timeline_events = sqlite_repo.get_timeline_events(case_id)
    documents = sqlite_repo.get_documents(case_id)

    people: dict[str, dict] = {}
    for entity in people_entities:
        name = _normalize_name(entity["value"])
        if not name or len(name) < 3:
            continue
        key = name.lower()
        if key not in people:
            role = KNOWN_ROLES.get(key, entity.get("context_snippet", "unknown"))
            if len(role) > 30:
                role = "unknown"
            people[key] = {"name": name, "role": role, "doc_ids": set()}
        people[key]["doc_ids"].add(entity["doc_id"])

    people = _merge_name_variants(people)
    people = {k: v for k, v in people.items() if not _is_victim(k)}

    if not people:
        logger.warning(f"No suspects found for case {case_id}")
        return

    doc_map = {d["doc_id"]: d for d in documents}
    forensic_doc_types = {"forensic_report", "autopsy_report", "cctv_transcript",
                           "security_log", "evidence_inventory", "phone_record"}

    # ── PHASE 1: free local sub-scores + gather text for motive scoring ─────
    computed: dict[str, dict] = {}
    motive_candidates = []  # entries needing an LLM motive score
    for key, person_data in people.items():
        name = person_data["name"]
        role = person_data["role"]
        doc_ids = person_data["doc_ids"]

        contradiction_count = sum(
            1 for c in contradictions
            if name.lower() in c["claim_a"].lower() or name.lower() in c["claim_b"].lower()
        )
        contradiction_score = min(100.0, contradiction_count * 20.0)

        events_mentioning = [e for e in timeline_events if name.lower() in e["description"].lower()]
        alibi_events = [
            e for e in events_mentioning
            if any(w in e["description"].lower() for w in ["alibi", "confirmed", "receipt", "restaurant", "dinner"])
        ]
        total_windows = max(1, len(events_mentioning))
        unaccounted = total_windows - len(alibi_events)
        opportunity_score = min(100.0, (unaccounted / total_windows) * 100)

        evidence_docs = [
            d for did in doc_ids
            if (d := doc_map.get(did)) and d.get("doc_type") in forensic_doc_types
        ]
        evidence_strength = min(100.0, len(evidence_docs) * 25.0)

        chunks = retriever.retrieve_for_entity(case_id, name, k=4)
        relevant_text = "\n\n".join(c["text"] for c in chunks)

        computed[key] = {
            "name": name, "role": role,
            "contradiction_count": contradiction_count,
            "contradiction_score": contradiction_score,
            "opportunity_score": opportunity_score,
            "evidence_strength": evidence_strength,
            "motive_score": 30.0,  # default until Phase 2 fills it in
            "motive_summary": "No strong motive evidence identified.",
        }
        if relevant_text.strip():
            motive_candidates.append({"key": key, "name": name, "text": relevant_text})

    # ── PHASE 2: ONE batched LLM call for motive scores ──────────────────────
    if motive_candidates:
        try:
            prompt = build_batch_motive_prompt(motive_candidates)
            results = llm_client.generate_json(
                prompt,
                system_instruction="You are a criminal profiler. Score motives objectively. Return JSON only."
            )
            if isinstance(results, list):
                by_name = {r.get("name", "").strip().lower(): r for r in results if isinstance(r, dict)}
                for mc in motive_candidates:
                    r = by_name.get(mc["name"].strip().lower())
                    if r and "score" in r:
                        try:
                            computed[mc["key"]]["motive_score"] = min(100.0, max(0.0, float(r["score"])))
                            computed[mc["key"]]["motive_summary"] = r.get("summary", "")
                        except (TypeError, ValueError):
                            pass
        except Exception as e:
            logger.error(f"Batched motive scoring failed: {e}")

    # ── PHASE 3: combine and store ────────────────────────────────────────────
    for key, c in computed.items():
        total_score = (
            0.30 * c["opportunity_score"] +
            0.25 * c["motive_score"] +
            0.25 * c["contradiction_score"] +
            0.20 * c["evidence_strength"]
        )
        sqlite_repo.upsert_suspect(
            name=c["name"],
            case_id=case_id,
            role=c["role"],
            opportunity_score=round(c["opportunity_score"], 1),
            motive_score=round(c["motive_score"], 1),
            contradiction_count=c["contradiction_count"],
            evidence_strength=round(c["evidence_strength"], 1),
            total_score=round(total_score, 1),
            motive_summary=c["motive_summary"]
        )
        logger.info(f"{c['name']}: total={total_score:.0f} opp={c['opportunity_score']:.0f} "
                    f"mot={c['motive_score']:.0f} con={c['contradiction_score']:.0f} ev={c['evidence_strength']:.0f}")

    logger.info(f"Suspect scoring complete: {len(computed)} suspects "
                f"(1 batched motive call for {len(motive_candidates)} of them)")