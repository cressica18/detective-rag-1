"""Documents router — status, list, and detail endpoints."""
from fastapi import APIRouter, HTTPException
from app.models.schemas import CaseStatusResponse, DocumentInfo, DocumentDetail, ChunkInfo
from app.repositories import sqlite_repo
from app.routers.upload import get_processing_status

router = APIRouter(prefix="/documents")


@router.get("/status/{case_id}", response_model=CaseStatusResponse)
async def get_status(case_id: str):
    """Poll ingestion status for a case."""
    proc = get_processing_status(case_id)
    case = sqlite_repo.get_case(case_id)

    status = proc.get("status", "unknown")
    if case and status == "unknown":
        status = case.get("status", "unknown")

    doc_count = len(sqlite_repo.get_documents(case_id))

    return CaseStatusResponse(
        case_id=case_id,
        status=status,
        message=proc.get("message", ""),
        doc_count=doc_count
    )


@router.get("/{case_id}", response_model=list[DocumentInfo])
async def list_documents(case_id: str):
    """List all documents for a case."""
    docs = sqlite_repo.get_documents(case_id)
    if not docs:
        case = sqlite_repo.get_case(case_id)
        if not case:
            raise HTTPException(404, f"Case {case_id} not found")
    return [
        DocumentInfo(
            doc_id=d["doc_id"],
            case_id=d["case_id"],
            filename=d["filename"],
            doc_type=d["doc_type"],
            page_count=d["page_count"],
            chunk_count=d.get("chunk_count", 0)
        )
        for d in docs
    ]


@router.get("/{case_id}/{doc_id}", response_model=DocumentDetail)
async def get_document(case_id: str, doc_id: str):
    """Get full document with chunks for Evidence Viewer."""
    doc = sqlite_repo.get_document(doc_id)
    if not doc or doc["case_id"] != case_id:
        raise HTTPException(404, "Document not found")

    chunks_raw = sqlite_repo.get_chunks_for_doc(doc_id)
    chunks = [
        ChunkInfo(
            chunk_id=c["chunk_id"],
            chunk_index=c["chunk_index"],
            page=c["page"],
            text=c["text"],
            char_start=c.get("char_start", 0),
            char_end=c.get("char_end", 0)
        )
        for c in chunks_raw
    ]

    return DocumentDetail(
        doc_id=doc_id,
        filename=doc["filename"],
        doc_type=doc["doc_type"],
        page_count=doc["page_count"],
        chunks=chunks
    )
