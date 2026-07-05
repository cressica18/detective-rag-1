"""ID generation utilities."""
import uuid
import hashlib


def new_uuid() -> str:
    return str(uuid.uuid4())


def stable_id(*parts: str) -> str:
    """Generate a stable, deterministic ID from parts."""
    combined = "|".join(parts)
    return hashlib.sha1(combined.encode()).hexdigest()[:16]


def chunk_id(doc_id: str, chunk_index: int) -> str:
    return f"{doc_id}_chunk_{chunk_index:04d}"
