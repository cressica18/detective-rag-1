"""Entity extractor — LLM-assisted structured extraction per document."""
import json
from app.services import llm_client
from app.services.prompt_builder import build_entity_extraction_prompt
from app.repositories import sqlite_repo
from app.utils.logging import get_logger

logger = get_logger(__name__)


def extract_and_store_entities(case_id: str, doc_id: str, filename: str, text: str):
    """Extract entities from document text and store in SQLite."""
    prompt = build_entity_extraction_prompt(text, filename)
    system = "You are a forensic document analyst. Extract entities precisely. Return ONLY valid JSON."

    result = llm_client.generate_json(prompt, system_instruction=system)
    if not result:
        logger.warning(f"Entity extraction returned empty for {filename}")
        return

    # Store people
    for person in result.get("people", []):
        name = person.get("name", "").strip()
        if name:
            sqlite_repo.insert_entity(
                case_id, doc_id, "person", name,
                person.get("role", "")
            )

    # Store times
    for time_ref in result.get("times", []):
        raw = time_ref.get("raw", "").strip()
        context = time_ref.get("context", "")
        if raw:
            sqlite_repo.insert_entity(
                case_id, doc_id, "time",
                raw,
                f"{context} [normalized: {time_ref.get('normalized', 'unknown')}]"
            )

    # Store locations
    for loc in result.get("locations", []):
        if loc.strip():
            sqlite_repo.insert_entity(case_id, doc_id, "location", loc.strip(), "")

    # Store objects
    for obj in result.get("objects", []):
        if obj.strip():
            sqlite_repo.insert_entity(case_id, doc_id, "object", obj.strip(), "")

    # Store claims (person + time + location + action tuples)
    for claim in result.get("claims", []):
        person = claim.get("person", "").strip()
        if person:
            context = (f"time={claim.get('time','')} | loc={claim.get('location','')} | "
                      f"action={claim.get('action','')}")
            sqlite_repo.insert_entity(case_id, doc_id, "claim", person, context)

    logger.info(f"Entities stored for {filename}: {len(result.get('people',[]))} people, "
                f"{len(result.get('times',[]))} times, {len(result.get('claims',[]))} claims")
