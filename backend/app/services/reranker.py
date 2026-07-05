"""Reranker — heuristic weighted reranking of candidate chunks."""
import re
from typing import Optional

DOC_TYPE_PRIORITIES = {
    "police_report": 0.8,
    "forensic_report": 0.9,
    "autopsy_report": 0.9,
    "cctv_transcript": 0.85,
    "security_log": 0.85,
    "phone_record": 0.75,
    "interview": 0.7,
    "witness_statement": 0.7,
    "evidence_inventory": 0.8,
    "unknown": 0.5,
}

QUERY_TYPE_HINTS = {
    "time": ["cctv_transcript", "security_log", "phone_record", "police_report"],
    "location": ["cctv_transcript", "security_log", "police_report", "witness_statement"],
    "forensic": ["forensic_report", "autopsy_report", "evidence_inventory"],
    "motive": ["interview", "witness_statement"],
    "alibi": ["interview", "witness_statement", "phone_record"],
    "evidence": ["forensic_report", "evidence_inventory", "police_report"],
}


def _infer_query_type(query: str) -> Optional[str]:
    q = query.lower()
    if any(w in q for w in ["when", "time", "clock", "pm", "am", "hour", "timestamp"]):
        return "time"
    if any(w in q for w in ["where", "location", "place", "gallery", "office", "corridor"]):
        return "location"
    if any(w in q for w in ["forensic", "dna", "fingerprint", "blood", "evidence", "exhibit"]):
        return "forensic"
    if any(w in q for w in ["motive", "reason", "why", "dispute", "argument"]):
        return "motive"
    if any(w in q for w in ["alibi", "confirmed", "witness"]):
        return "alibi"
    return None


def _jaccard_similarity(a: str, b: str, n: int = 3) -> float:
    """Compute Jaccard similarity of character n-grams."""
    shingles_a = set(a[i:i+n] for i in range(len(a) - n + 1))
    shingles_b = set(b[i:i+n] for i in range(len(b) - n + 1))
    if not shingles_a or not shingles_b:
        return 0.0
    intersection = len(shingles_a & shingles_b)
    union = len(shingles_a | shingles_b)
    return intersection / union if union > 0 else 0.0


def rerank(chunks: list[dict], query: str, top_k: int = 5) -> list[dict]:
    """
    Rerank candidate chunks using heuristic weighted score.
    score = 0.7*cosine_similarity + 0.2*doc_type_bonus + 0.1*entity_match_bonus
    Drop near-duplicate chunks (Jaccard > 0.85).
    """
    if not chunks:
        return []

    query_type = _infer_query_type(query)
    preferred_types = QUERY_TYPE_HINTS.get(query_type, []) if query_type else []
    query_words = set(re.findall(r"\b\w+\b", query.lower()))

    scored = []
    for c in chunks:
        cosine_sim = c.get("similarity", 0.5)

        # Doc type bonus
        doc_type = c.get("doc_type", "unknown")
        base_type_score = DOC_TYPE_PRIORITIES.get(doc_type, 0.5)
        type_match_bonus = 1.0 if doc_type in preferred_types else base_type_score
        doc_type_score = (type_match_bonus + base_type_score) / 2

        # Entity/keyword match bonus
        text_words = set(re.findall(r"\b\w+\b", c.get("text", "").lower()))
        overlap = len(query_words & text_words) / max(len(query_words), 1)
        entity_bonus = min(1.0, overlap * 2)

        score = 0.7 * cosine_sim + 0.2 * doc_type_score + 0.1 * entity_bonus
        scored.append({**c, "rerank_score": score})

    scored.sort(key=lambda x: x["rerank_score"], reverse=True)

    # Deduplicate near-identical chunks
    deduplicated = []
    for chunk in scored:
        is_dup = False
        for kept in deduplicated:
            if _jaccard_similarity(chunk["text"][:300], kept["text"][:300]) > 0.85:
                is_dup = True
                break
        if not is_dup:
            deduplicated.append(chunk)
        if len(deduplicated) >= top_k:
            break

    return deduplicated
