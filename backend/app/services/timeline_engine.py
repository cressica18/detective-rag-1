"""Timeline engine — normalizes extracted times into chronological event list."""
import re
from dateutil import parser as dateutil_parser
from app.repositories import sqlite_repo
from app.utils.ids import stable_id
from app.utils.logging import get_logger

logger = get_logger(__name__)

CASE_DATE = "2024-03-15"  # The Riverside Museum Murder date


def normalize_time(raw_time: str) -> str:
    """
    Normalize a raw time string to HH:MM or return the raw string if unparseable.
    """
    if not raw_time:
        return raw_time
    # Clean up common patterns
    cleaned = raw_time.strip().lower()
    cleaned = re.sub(r"around|approximately|about|circa|roughly", "", cleaned).strip()
    cleaned = re.sub(r"(quarter past)\s*(\d+)", lambda m: f"{int(m.group(2))}:15", cleaned)
    cleaned = re.sub(r"(quarter to)\s*(\d+)", lambda m: f"{int(m.group(2))-1}:45", cleaned)
    cleaned = re.sub(r"(half past)\s*(\d+)", lambda m: f"{int(m.group(2))}:30", cleaned)

    # Try dateutil parsing
    try:
        dt = dateutil_parser.parse(f"{CASE_DATE} {cleaned}", fuzzy=True)
        return dt.strftime("%H:%M")
    except Exception:
        pass

    # Try just the number with pm/am
    match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", cleaned)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        ampm = match.group(3)
        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"

    return raw_time  # Return raw if we can't normalize


def build_and_store_timeline(case_id: str):
    """Build timeline from extracted time entities and store in SQLite."""
    sqlite_repo.delete_timeline_for_case(case_id)

    time_entities = sqlite_repo.get_entities(case_id, entity_type="time")
    if not time_entities:
        logger.warning(f"No time entities for case {case_id}")
        return

    # Get contradictions for cross-referencing
    contradictions = sqlite_repo.get_contradictions(case_id)
    contradicted_docs = set()
    for c in contradictions:
        contradicted_docs.add(c["claim_a_doc_id"])
        contradicted_docs.add(c["claim_b_doc_id"])

    # Build events from time entities
    events = []
    seen_descriptions = []

    for entity in time_entities:
        raw_time = entity["value"]
        context = entity["context_snippet"]
        doc_id = entity["doc_id"]

        normalized = normalize_time(raw_time)
        # Extract a cleaner description from context snippet
        description = context.replace("normalized: unknown", "").replace(f"[normalized: {normalized}]", "").strip()
        if description.startswith("action="):
            description = description[7:]
        # Clean up the format
        description = re.sub(r"time=\S*\s*\|?\s*", "", description)
        description = re.sub(r"loc=([^|]+)\s*\|?\s*", r"at \1 ", description)
        description = description.strip(" |")
        if not description:
            description = f"Event at {raw_time}"

        # Simple deduplication: skip if very similar to existing
        is_dup = False
        for seen_desc in seen_descriptions:
            if _text_similarity(description, seen_desc) > 0.7:
                is_dup = True
                break
        if is_dup:
            continue

        is_contradicted = doc_id in contradicted_docs
        event_id = stable_id(case_id, doc_id, raw_time, description[:30])

        events.append({
            "event_id": event_id,
            "timestamp": normalized,
            "raw_timestamp": raw_time,
            "description": description[:200],
            "doc_id": doc_id,
            "is_contradicted": is_contradicted
        })
        seen_descriptions.append(description)

    # Sort by timestamp
    def sort_key(e):
        ts = e["timestamp"]
        try:
            # Parse HH:MM
            parts = ts.split(":")
            if len(parts) >= 2:
                return int(parts[0]) * 60 + int(parts[1])
        except Exception:
            pass
        return 9999  # Unknown times go to end

    events.sort(key=sort_key)

    # Store in SQLite
    for event in events:
        sqlite_repo.insert_timeline_event(
            event_id=event["event_id"],
            case_id=case_id,
            timestamp=event["timestamp"],
            description=event["description"],
            source_doc_ids=[event["doc_id"]],
            is_contradicted=event["is_contradicted"]
        )

    logger.info(f"Timeline built: {len(events)} events for case {case_id}")


def _text_similarity(a: str, b: str) -> float:
    """Simple word-overlap similarity."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = len(words_a & words_b)
    union = len(words_a | words_b)
    return intersection / union
