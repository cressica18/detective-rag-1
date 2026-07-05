"""Suspect scorer — computes 4 sub-scores and total suspicion score per suspect."""
from app.repositories import sqlite_repo
from app.services import llm_client, retriever
from app.services.prompt_builder import build_motive_score_prompt
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Known person roles for the sample case — augmented dynamically
KNOWN_ROLES = {
    "eleanor voss": "victim",
    "marcus bellweather": "suspect",
    "lydia ferro": "suspect",
    "tobias reyes": "suspect",
}


def score_and_store_suspects(case_id: str):
    """Compute suspect scores for all identified persons and store in SQLite."""
    sqlite_repo.delete_suspects_for_case(case_id)

    # Get all known people from entity extraction
    people_entities = sqlite_repo.get_entities(case_id, entity_type="person")
    contradictions = sqlite_repo.get_contradictions(case_id)
    timeline_events = sqlite_repo.get_timeline_events(case_id)
    documents = sqlite_repo.get_documents(case_id)

    # Aggregate unique people (by name, case-insensitive)
    people: dict[str, dict] = {}
    for entity in people_entities:
        name = entity["value"].strip()
        if not name or len(name) < 3:
            continue
        key = name.lower()
        if key not in people:
            role = KNOWN_ROLES.get(key, entity.get("context_snippet", "unknown"))
            if len(role) > 30:
                role = "unknown"
            people[key] = {"name": name, "role": role, "doc_ids": set()}
        people[key]["doc_ids"].add(entity["doc_id"])

    # Skip victim
    people = {k: v for k, v in people.items()
              if not any(x in k for x in ["eleanor voss", "victim"])}

    if not people:
        logger.warning(f"No suspects found for case {case_id}")
        return

    doc_map = {d["doc_id"]: d for d in documents}

    for key, person_data in people.items():
        name = person_data["name"]
        role = person_data["role"]
        doc_ids = person_data["doc_ids"]
        logger.info(f"Scoring suspect: {name}")

        # ── CONTRADICTION SCORE (25%) ──────────────────────────────────────────
        contradiction_count = sum(
            1 for c in contradictions
            if name.lower() in c["claim_a"].lower() or name.lower() in c["claim_b"].lower()
        )
        contradiction_score = min(100.0, contradiction_count * 20.0)

        # ── OPPORTUNITY SCORE (30%) ────────────────────────────────────────────
        # Count timeline events with no confirmed alibi for this person
        # Events where they're mentioned as being somewhere vs unaccounted windows
        events_mentioning = [
            e for e in timeline_events
            if name.lower() in e["description"].lower()
        ]
        alibi_events = [
            e for e in events_mentioning
            if any(w in e["description"].lower() for w in ["alibi", "confirmed", "receipt", "restaurant", "dinner"])
        ]
        total_windows = max(1, len(events_mentioning))
        unaccounted = total_windows - len(alibi_events)
        opportunity_score = min(100.0, (unaccounted / total_windows) * 100)

        # ── EVIDENCE STRENGTH (20%) ────────────────────────────────────────────
        forensic_doc_types = {"forensic_report", "autopsy_report", "cctv_transcript",
                               "security_log", "evidence_inventory", "phone_record"}
        evidence_docs = [
            d for did in doc_ids
            if (d := doc_map.get(did)) and d.get("doc_type") in forensic_doc_types
        ]
        evidence_strength = min(100.0, len(evidence_docs) * 25.0)

        # ── MOTIVE SCORE (25%) ────────────────────────────────────────────────
        # Retrieve relevant text for this suspect
        chunks = retriever.retrieve_for_entity(case_id, name, k=4)
        relevant_text = "\n\n".join(c["text"] for c in chunks)
        motive_score = 30.0  # default
        motive_summary = "No strong motive evidence identified."

        if relevant_text.strip():
            try:
                prompt = build_motive_score_prompt(name, relevant_text)
                result = llm_client.generate_json(
                    prompt,
                    system_instruction="You are a criminal profiler. Score motives objectively. Return JSON only."
                )
                if result and "score" in result:
                    motive_score = min(100.0, max(0.0, float(result["score"])))
                    motive_summary = result.get("summary", "")
            except Exception as e:
                logger.error(f"Motive scoring error for {name}: {e}")

        # ── TOTAL SCORE ────────────────────────────────────────────────────────
        total_score = (
            0.30 * opportunity_score +
            0.25 * motive_score +
            0.25 * contradiction_score +
            0.20 * evidence_strength
        )

        sqlite_repo.upsert_suspect(
            name=name,
            case_id=case_id,
            role=role,
            opportunity_score=round(opportunity_score, 1),
            motive_score=round(motive_score, 1),
            contradiction_count=contradiction_count,
            evidence_strength=round(evidence_strength, 1),
            total_score=round(total_score, 1),
            motive_summary=motive_summary
        )
        logger.info(f"{name}: total={total_score:.0f} opp={opportunity_score:.0f} "
                   f"mot={motive_score:.0f} con={contradiction_score:.0f} ev={evidence_strength:.0f}")
