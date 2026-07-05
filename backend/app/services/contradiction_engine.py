"""Contradiction engine — hybrid rule-based + LLM detection."""
from collections import defaultdict
from app.repositories import sqlite_repo
from app.services import llm_client
from app.services.prompt_builder import build_contradiction_check_prompt
from app.utils.ids import stable_id
from app.utils.logging import get_logger

logger = get_logger(__name__)


def detect_and_store_contradictions(case_id: str):
    """
    Run contradiction detection across all claim entities for a case.
    Stores confirmed contradictions in SQLite.
    """
    # Delete existing contradictions for clean rebuild
    sqlite_repo.delete_contradictions_for_case(case_id)

    # Get all claims
    claims = sqlite_repo.get_entities(case_id, entity_type="claim")
    if not claims:
        logger.warning(f"No claims found for case {case_id}")
        return

    # Group by person name
    by_person: dict[str, list[dict]] = defaultdict(list)
    for claim in claims:
        person = claim["value"].strip()
        if person:
            by_person[person].append(claim)

    # Get document map for filenames
    docs = {d["doc_id"]: d for d in sqlite_repo.get_documents(case_id)}

    contradiction_count = 0
    for person, person_claims in by_person.items():
        if len(person_claims) < 2:
            continue

        # Compare each pair of claims for this person
        for i in range(len(person_claims)):
            for j in range(i + 1, len(person_claims)):
                c_a = person_claims[i]
                c_b = person_claims[j]

                # Skip if same doc
                if c_a["doc_id"] == c_b["doc_id"]:
                    continue

                claim_a_text = c_a["context_snippet"]
                claim_b_text = c_b["context_snippet"]

                # Quick rule-based pre-filter: must both mention time or location
                has_time_a = any(w in claim_a_text.lower() for w in ["time=", "pm", "am", "hour", ":"])
                has_time_b = any(w in claim_b_text.lower() for w in ["time=", "pm", "am", "hour", ":"])
                has_loc_a = "loc=" in claim_a_text.lower()
                has_loc_b = "loc=" in claim_b_text.lower()

                if not ((has_time_a or has_loc_a) and (has_time_b or has_loc_b)):
                    continue

                doc_a = docs.get(c_a["doc_id"], {})
                doc_b = docs.get(c_b["doc_id"], {})
                source_a = doc_a.get("filename", c_a["doc_id"])
                source_b = doc_b.get("filename", c_b["doc_id"])

                # Ask LLM to verify
                prompt = build_contradiction_check_prompt(
                    f"{person}: {claim_a_text}", source_a,
                    f"{person}: {claim_b_text}", source_b
                )
                result = llm_client.generate_json(
                    prompt,
                    system_instruction="You are a fact-checker for a criminal investigation. Answer in JSON only."
                )

                if result.get("conflict") is True:
                    cid = stable_id(case_id, c_a["doc_id"], c_b["doc_id"], str(i), str(j))
                    explanation = result.get("explanation", "Conflicting claims detected.")
                    sqlite_repo.insert_contradiction(
                        id=cid,
                        case_id=case_id,
                        claim_a=f"{person}: {claim_a_text}",
                        claim_a_doc_id=c_a["doc_id"],
                        claim_b=f"{person}: {claim_b_text}",
                        claim_b_doc_id=c_b["doc_id"],
                        explanation=explanation
                    )
                    contradiction_count += 1
                    logger.info(f"Contradiction found for {person}: {explanation}")

                # Limit API calls per run
                if contradiction_count >= 10:
                    return

    logger.info(f"Contradiction detection complete: {contradiction_count} contradictions found")
