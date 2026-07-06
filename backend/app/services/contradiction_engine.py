"""Contradiction engine — hybrid rule-based + LLM detection (single batched LLM call)."""
from collections import defaultdict
from app.repositories import sqlite_repo
from app.services import llm_client
from app.services.prompt_builder import build_batch_contradiction_prompt
from app.utils.ids import stable_id
from app.utils.logging import get_logger

logger = get_logger(__name__)

MAX_PAIRS = 20  # cap prompt/output size and quota usage


def detect_and_store_contradictions(case_id: str):
    """
    Run contradiction detection across all claim entities for a case.
    Collects candidate pairs via rule-based prefilter (free), then verifies
    all of them in a SINGLE batched LLM call to minimize quota usage.
    """
    sqlite_repo.delete_contradictions_for_case(case_id)

    claims = sqlite_repo.get_entities(case_id, entity_type="claim")
    if not claims:
        logger.warning(f"No claims found for case {case_id}")
        return

    by_person: dict[str, list[dict]] = defaultdict(list)
    for claim in claims:
        person = claim["value"].strip()
        if person:
            by_person[person].append(claim)

    docs = {d["doc_id"]: d for d in sqlite_repo.get_documents(case_id)}

    # Phase 1: collect all candidate pairs (rule-based, no LLM calls)
    candidates = []
    for person, person_claims in by_person.items():
        if len(person_claims) < 2:
            continue
        for i in range(len(person_claims)):
            for j in range(i + 1, len(person_claims)):
                c_a = person_claims[i]
                c_b = person_claims[j]
                if c_a["doc_id"] == c_b["doc_id"]:
                    continue

                claim_a_text = c_a["context_snippet"]
                claim_b_text = c_b["context_snippet"]

                has_time_a = any(w in claim_a_text.lower() for w in ["time=", "pm", "am", "hour", ":"])
                has_time_b = any(w in claim_b_text.lower() for w in ["time=", "pm", "am", "hour", ":"])
                has_loc_a = "loc=" in claim_a_text.lower()
                has_loc_b = "loc=" in claim_b_text.lower()

                if not ((has_time_a or has_loc_a) and (has_time_b or has_loc_b)):
                    continue

                doc_a = docs.get(c_a["doc_id"], {})
                doc_b = docs.get(c_b["doc_id"], {})

                candidates.append({
                    "person": person,
                    "c_a": c_a, "c_b": c_b,
                    "claim_a": claim_a_text, "claim_b": claim_b_text,
                    "source_a": doc_a.get("filename", c_a["doc_id"]),
                    "source_b": doc_b.get("filename", c_b["doc_id"]),
                })

    if not candidates:
        logger.info(f"Contradiction detection complete: no candidate pairs for case {case_id}")
        return

    candidates = candidates[:MAX_PAIRS]
    for idx, c in enumerate(candidates):
        c["index"] = idx

    # Phase 2: ONE batched LLM call to verify all candidates at once
    prompt = build_batch_contradiction_prompt(candidates)
    try:
        results = llm_client.generate_json(
            prompt,
            system_instruction="You are a fact-checker for a criminal investigation. Answer in JSON only."
        )
    except Exception as e:
        logger.error(f"Batched contradiction check failed: {e}")
        return

    if not isinstance(results, list):
        logger.warning(f"Contradiction batch response was not a list for case {case_id}")
        return

    results_by_index = {}
    for r in results:
        if isinstance(r, dict) and "index" in r:
            try:
                results_by_index[int(r["index"])] = r
            except (TypeError, ValueError):
                continue

    contradiction_count = 0
    for c in candidates:
        r = results_by_index.get(c["index"])
        if r and r.get("conflict") is True:
            cid = stable_id(case_id, c["c_a"]["doc_id"], c["c_b"]["doc_id"], str(c["index"]))
            explanation = r.get("explanation", "Conflicting claims detected.")
            sqlite_repo.insert_contradiction(
                id=cid,
                case_id=case_id,
                claim_a=f"{c['person']}: {c['claim_a']}",
                claim_a_doc_id=c["c_a"]["doc_id"],
                claim_b=f"{c['person']}: {c['claim_b']}",
                claim_b_doc_id=c["c_b"]["doc_id"],
                explanation=explanation
            )
            contradiction_count += 1
            logger.info(f"Contradiction found for {c['person']}: {explanation}")

    logger.info(f"Contradiction detection complete: {contradiction_count} contradictions found "
                f"(checked {len(candidates)} candidate pairs in 1 LLM call)")