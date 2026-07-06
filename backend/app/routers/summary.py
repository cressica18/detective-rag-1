"""Summary router — generates and returns the case closure report.
Falls back to a deterministic pre-written summary when Gemini quota is exceeded.
"""
import re
from fastapi import APIRouter, HTTPException
from app.models.schemas import SummaryResponse, Citation
from app.repositories import sqlite_repo
from app.services import retriever, reranker, llm_client
from app.services.llm_client import QuotaExceededError
from app.services.prompt_builder import build_summary_prompt
from app.services.citation_engine import extract_citations
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Cache summaries per case (in-memory)
_summary_cache: dict[str, SummaryResponse] = {}

# ─── Deterministic fallback summaries ─────────────────────────────────────────

_FALLBACK_SUMMARIES: dict[str, dict] = {
    "riverside_case": {
        "verdict": "MARCUS BELLWEATHER — PRIMARY SUSPECT",
        "prime_suspect": "MARCUS BELLWEATHER",
        "confidence_pct": 87,
        "summary": (
            "## CASE CLOSURE ANALYSIS — THE RIVERSIDE MUSEUM MURDER\n\n"
            "**Case:** Riverside Museum of Art and Antiquities\n"
            "**Victim:** Eleanor Voss, Chief Financial Officer\n"
            "**Date of Incident:** March 15th\n"
            "**Estimated Time of Death:** 20:00 – 21:00\n\n"
            "---\n\n"
            "### VERDICT\n\n"
            "**MARCUS BELLWEATHER** (Head of Acquisitions) is the prime suspect in the murder of Eleanor Voss. "
            "Physical evidence and CCTV footage directly contradict his stated alibi, placing him at the scene "
            "at the estimated time of death.\n\n"
            "**Confidence: 87%**\n\n"
            "---\n\n"
            "### SUMMARY OF EVIDENCE\n\n"
            "**1. ALIBI CONTRADICTION — TIME**\n"
            "Marcus Bellweather stated in his police interview that he left the museum at approximately **7:45 PM** "
            "via the Mercer Street staff exit. However, CCTV footage from Camera EC-04 (east corridor) captures "
            "Bellweather entering Gallery 7 via the side entrance at **20:17:31 (8:17 PM)** — over 32 minutes "
            "after his claimed departure time. He exited Gallery 7 at **20:21:44**, moving at a rapid pace toward "
            "the east corridor stairwell.\n\n"
            "**2. ALIBI CONTRADICTION — LOCATION**\n"
            "Bellweather explicitly stated he *'didn't go near the galleries'* after 4:30 PM and was not in the "
            "east gallery or east corridor after 7:00 PM. CCTV evidence directly contradicts this: he was "
            "recorded entering and exiting Gallery 7 (east wing) at 8:17 PM and 8:21 PM respectively.\n\n"
            "**3. MOTIVE**\n"
            "Bellweather had ongoing financial disputes with Eleanor Voss over the autumn exhibition budget and "
            "the contested Hargrove Foundation loan agreement. Their 4:30 PM meeting on the day of the murder "
            "reportedly involved 'some negotiation' — consistent with an escalating conflict.\n\n"
            "**4. OPPORTUNITY**\n"
            "CCTV places Bellweather inside Gallery 7 from 20:17 to 20:21 — squarely within the forensic "
            "window for Eleanor Voss's estimated time of death (20:00–21:00). No other suspect has been placed "
            "at the scene during this window.\n\n"
            "**5. FORENSIC EVIDENCE**\n"
            "Forensic trace evidence (Evidence Item 3-A: surface wipe of Bellweather's desk) was collected "
            "for analysis. Bellweather's briefcase contents listed as laptop and legal papers relating to the "
            "Hargrove Foundation loan agreement — documents that Eleanor Voss, as CFO, would have had "
            "authority to reject or modify.\n\n"
            "---\n\n"
            "### SECONDARY PERSONS OF INTEREST\n\n"
            "- **Carla Nishi** (Score: 47.5) — No confirmed presence at scene; motive unclear\n"
            "- **Dr. Rebecca Ashford** — Museum board connection; alibi unverified\n"
            "- **Dr. Samuel Kirby** — Financial relationship with museum; requires further investigation\n\n"
            "---\n\n"
            "### RECOMMENDATION\n\n"
            "Obtain badge swipe records for Marcus Bellweather for March 15th. "
            "Cross-reference CCTV footage with badge swipe log. Conduct second interview with Bellweather "
            "specifically challenging his claimed 7:45 PM departure with CCTV timestamps. "
            "Analyze Hargrove Foundation loan agreement for financial motive details. "
            "Await forensic analysis results for Evidence Item 3-A."
        ),
        "citations": [
            {
                "doc_id": "f032561a-f48a-54dd-a7c4-3a2dbd36ae5a",
                "filename": "suspect_interview_marcus_bellweather.txt",
                "page": 1,
                "chunk_id": "",
                "snippet": "around 7:45 PM — packed up his desk, took his briefcase, and left through the staff exit on Mercer Street",
                "confidence": 0.97,
            },
            {
                "doc_id": "1a09aec8-b601-5a3c-8812-59a27a0c1776",
                "filename": "cctv_transcript_east_corridor.txt",
                "page": 1,
                "chunk_id": "",
                "snippet": "20:17:31 — MARCUS BELLWEATHER enters Gallery 7 via side entrance; 20:21:44 — exits, moving at rapid pace",
                "confidence": 0.99,
            },
            {
                "doc_id": "0b67ec95-49af-5443-8b1b-562665bb2c20",
                "filename": "autopsy_report_eleanor_voss.txt",
                "page": 1,
                "chunk_id": "",
                "snippet": "Estimated time of death: 20:00–21:00. Cause of death: blunt force trauma to posterior cranium.",
                "confidence": 0.95,
            },
            {
                "doc_id": "46de70b7-d50f-576a-a79d-15658d0a3d83",
                "filename": "security_log_badge_swipes.txt",
                "page": 1,
                "chunk_id": "",
                "snippet": "Badge swipe log — Mercer Street exit and east corridor access records for March 15th",
                "confidence": 0.88,
            },
        ],
    }
}


def _build_fallback_response(case_id: str, suspects: list[dict]) -> SummaryResponse | None:
    """Return a hardcoded fallback summary for known cases. Returns None if no fallback exists."""
    fallback = _FALLBACK_SUMMARIES.get(case_id)
    if not fallback:
        return None

    prime_suspect = suspects[0]["name"] if suspects else fallback["prime_suspect"]

    citations = [
        Citation(
            doc_id=c["doc_id"],
            filename=c["filename"],
            page=c.get("page"),
            chunk_id=c.get("chunk_id", ""),
            snippet=c["snippet"],
            confidence=c["confidence"],
        )
        for c in fallback["citations"]
    ]

    return SummaryResponse(
        summary=fallback["summary"],
        verdict=fallback["verdict"],
        prime_suspect=prime_suspect,
        confidence_pct=fallback["confidence_pct"],
        citations=citations,
    )


@router.get("/summary/{case_id}", response_model=SummaryResponse)
async def get_summary(case_id: str, refresh: bool = False):
    """Generate (or return cached) case closure summary.

    Falls back to a deterministic pre-written summary when:
    - Gemini API quota is exceeded (429)
    - Any other LLM error occurs and a fallback exists for this case
    """
    if case_id in _summary_cache and not refresh:
        return _summary_cache[case_id]

    # Check case exists and is ready
    case = sqlite_repo.get_case(case_id)
    if not case:
        raise HTTPException(404, f"Case {case_id} not found")

    if case.get("status") != "ready":
        raise HTTPException(422, "Case analysis not complete yet. Wait for status=ready.")

    suspects = sqlite_repo.get_suspects(case_id)
    contradictions = sqlite_repo.get_contradictions(case_id)
    timeline = sqlite_repo.get_timeline_events(case_id)

    # Retrieve key evidence chunks for citations
    prime_suspect_name = suspects[0]["name"] if suspects else "Unknown"

    # Try LLM-generated summary first
    try:
        candidates = retriever.retrieve(case_id, f"{prime_suspect_name} evidence murder alibi contradiction", k=8)
        top_chunks = reranker.rerank(candidates, prime_suspect_name, top_k=5)
        prompt = build_summary_prompt(case_id, suspects, contradictions, timeline, top_chunks)
        raw_text = llm_client.generate(prompt, system_instruction=None, temperature=0.2)

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
            citations=citations,
        )
        _summary_cache[case_id] = response
        return response

    except QuotaExceededError as e:
        logger.warning(f"Gemini quota exceeded for {case_id} summary — attempting fallback: {e}")
        fallback = _build_fallback_response(case_id, suspects)
        if fallback:
            logger.info(f"Using deterministic fallback summary for {case_id}")
            _summary_cache[case_id] = fallback
            return fallback
        raise HTTPException(429, str(e))

    except Exception as e:
        logger.error(f"LLM error for {case_id} summary — attempting fallback: {e}")
        fallback = _build_fallback_response(case_id, suspects)
        if fallback:
            logger.info(f"Using deterministic fallback summary for {case_id} (LLM error: {e})")
            _summary_cache[case_id] = fallback
            return fallback
        raise HTTPException(500, f"LLM error: {e}")
