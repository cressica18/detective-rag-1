"""Summary router — generates and returns the case closure report."""
import re
from fastapi import APIRouter, HTTPException
from app.models.schemas import SummaryResponse, Citation
from app.repositories import sqlite_repo
from app.services import retriever, reranker, llm_client
from app.services.prompt_builder import build_summary_prompt
from app.services.citation_engine import extract_citations
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Cache summaries per case (in-memory)
_summary_cache: dict[str, SummaryResponse] = {}


@router.get("/summary/{case_id}", response_model=SummaryResponse)
async def get_summary(case_id: str, refresh: bool = False):
    """Generate (or return cached) case closure summary."""
    if case_id in _summary_cache and not refresh:
        return _summary_cache[case_id]

    # Check case exists and is ready
    case = sqlite_repo.get_case(case_id)
    if not case:
        raise HTTPException(404, f"Case {case_id} not found")

    suspects = sqlite_repo.get_suspects(case_id)
    contradictions = sqlite_repo.get_contradictions(case_id)
    timeline = sqlite_repo.get_timeline_events(case_id)

    if not suspects and not contradictions:
        raise HTTPException(422, "Case analysis not complete yet. Wait for status=ready.")

    # Retrieve key evidence chunks for citations
    prime_suspect_name = suspects[0]["name"] if suspects else "Unknown"
    candidates = retriever.retrieve(case_id, f"{prime_suspect_name} evidence murder alibi contradiction", k=8)
    top_chunks = reranker.rerank(candidates, prime_suspect_name, top_k=5)

    # Generate summary
    prompt = build_summary_prompt(case_id, suspects, contradictions, timeline, top_chunks)
    try:
        raw_text = llm_client.generate(prompt, system_instruction=None, temperature=0.2)
    except Exception as e:
        raise HTTPException(500, f"LLM error: {e}")

    cleaned_text, citations = extract_citations(raw_text, top_chunks)

    # Extract verdict
    verdict = prime_suspect_name
    confidence_pct = 75
    verdict_match = re.search(r"VERDICT:\s*(.+?)(?:\.|$)", raw_text, re.IGNORECASE)
    if verdict_match:
        verdict = verdict_match.group(1).strip()
    conf_match = re.search(r"Confidence:\s*(\d+)%", raw_text, re.IGNORECASE)
    if conf_match:
        confidence_pct = int(conf_match.group(1))

    response = SummaryResponse(
        summary=cleaned_text,
        verdict=verdict,
        prime_suspect=prime_suspect_name,
        confidence_pct=confidence_pct,
        citations=citations
    )
    _summary_cache[case_id] = response
    return response
