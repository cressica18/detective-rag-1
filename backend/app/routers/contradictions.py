"""Contradictions router."""
from fastapi import APIRouter
from app.models.schemas import Contradiction, Citation
from app.repositories import sqlite_repo

router = APIRouter()


@router.get("/contradictions/{case_id}", response_model=list[Contradiction])
async def get_contradictions(case_id: str):
    rows = sqlite_repo.get_contradictions(case_id)
    docs = {d["doc_id"]: d for d in sqlite_repo.get_documents(case_id)}

    result = []
    for row in rows:
        def make_citation(doc_id: str, claim: str) -> Citation:
            doc = docs.get(doc_id, {})
            return Citation(
                doc_id=doc_id,
                filename=doc.get("filename", "unknown"),
                page=None,
                chunk_id="",
                snippet=claim[:200],
                confidence=0.0
            )

        result.append(Contradiction(
            id=row["id"],
            claim_a=row["claim_a"],
            claim_a_source=make_citation(row["claim_a_doc_id"], row["claim_a"]),
            claim_b=row["claim_b"],
            claim_b_source=make_citation(row["claim_b_doc_id"], row["claim_b"]),
            explanation=row["explanation"]
        ))
    return result
