"""Citation engine — maps [S#] tags in LLM responses to source metadata."""
import re
from app.models.schemas import Citation


def extract_citations(raw_text: str, chunks: list[dict]) -> tuple[str, list[Citation]]:
    """
    Parse [S#] tags from raw LLM response text.
    Returns (cleaned_text, citations_list).
    cleaned_text has [S#] replaced with [citation:N] placeholders the frontend renders.
    """
    # Find all [S#] references
    pattern = re.compile(r"\[S(\d+)\]")
    used_indices = set()
    for match in pattern.finditer(raw_text):
        idx = int(match.group(1))
        used_indices.add(idx)

    # Build citation objects for each used S#
    citation_map = {}
    citations = []
    for idx in sorted(used_indices):
        chunk_idx = idx - 1  # S1 → chunks[0]
        if 0 <= chunk_idx < len(chunks):
            chunk = chunks[chunk_idx]
            snippet = chunk["text"][:200].strip()
            if len(chunk["text"]) > 200:
                snippet += "..."
            citation = Citation(
                doc_id=chunk.get("doc_id", ""),
                filename=chunk.get("filename", "unknown"),
                page=chunk.get("page"),
                chunk_id=chunk.get("chunk_id", ""),
                snippet=snippet,
                confidence=round(chunk.get("similarity", 0.5) * 100, 1),
            )
            citation_map[idx] = len(citations)
            citations.append(citation)

    # Replace [S#] with [citation:N] placeholder
    def replace_tag(match: re.Match) -> str:
        idx = int(match.group(1))
        if idx in citation_map:
            return f"[citation:{citation_map[idx]}]"
        return match.group(0)

    cleaned_text = pattern.sub(replace_tag, raw_text)
    return cleaned_text, citations
