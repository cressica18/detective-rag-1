"""Entity extractor — LLM-assisted structured extraction per document."""
import json
from app.services import llm_client
from app.services.prompt_builder import build_entity_extraction_prompt
from app.repositories import sqlite_repo
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _s(value, default: str = "") -> str:
    """Coerce a possibly-None/non-string LLM field into a stripped string."""
    if value is None:
        return default
    return str(value).strip()


def extract_and_store_entities(case_id: str, doc_id: str, filename: str, text: str):
    """Extract entities from document text and store in SQLite."""
    prompt = build_entity_extraction_prompt(text, filename)
    system = "You are a forensic document analyst. Extract entities precisely. Return ONLY valid JSON."

    result = llm_client.generate_json(prompt, system_instruction=system)
    if not result:
        logger.warning(f"Entity extraction returned empty for {filename}")
        return

    # Store people
    for person in result.get("people", []) or []:
        name = _s(person.get("name"))
        if name:
            sqlite_repo.insert_entity(
                case_id, doc_id, "person", name,
                _s(person.get("role"))
            )

    # Store times
    for time_ref in result.get("times", []) or []:
        raw = _s(time_ref.get("raw"))
        context = _s(time_ref.get("context"))
        if raw:
            sqlite_repo.insert_entity(
                case_id, doc_id, "time",
                raw,
                f"{context} [normalized: {_s(time_ref.get('normalized'), 'unknown')}]"
            )

    # Store locations
    for loc in result.get("locations", []) or []:
        loc = _s(loc)
        if loc:
            sqlite_repo.insert_entity(case_id, doc_id, "location", loc, "")

    # Store objects
    for obj in result.get("objects", []) or []:
        obj = _s(obj)
        if obj:
            sqlite_repo.insert_entity(case_id, doc_id, "object", obj, "")

    # Store claims (person + time + location + action tuples)
    for claim in result.get("claims", []) or []:
        person = _s(claim.get("person"))
        if person:
            context = (f"time={_s(claim.get('time'))} | loc={_s(claim.get('location'))} | "
                      f"action={_s(claim.get('action'))}")
            sqlite_repo.insert_entity(case_id, doc_id, "claim", person, context)

    logger.info(f"Entities stored for {filename}: {len(result.get('people') or [])} people, "
                f"{len(result.get('times') or [])} times, {len(result.get('claims') or [])} claims")