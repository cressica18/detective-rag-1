"""Upload router — handles file ingestion and triggers processing pipeline."""
import os
import shutil
import threading
import traceback
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional

from app.config import settings
from app.models.schemas import UploadResponse
from app.repositories import sqlite_repo
from app.services import (
    document_parser, text_cleaner, chunker, embedder,
    entity_extractor, contradiction_engine, timeline_engine,
    suspect_scorer
)
from app.repositories import chroma_repo
from app.utils.ids import new_uuid
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
_processing_status: dict[str, dict] = {}


def get_processing_status(case_id: str) -> dict:
    return _processing_status.get(case_id, {"status": "unknown", "message": ""})


@router.post("/upload", response_model=UploadResponse)
async def upload_files(
    files: List[UploadFile] = File(...),
    case_id: Optional[str] = Form(None),
    case_name: Optional[str] = Form(None),
):
    """Accept uploaded files, validate, save, and trigger processing."""
    if not case_id:
        case_id = new_uuid()
    if not case_name:
        case_name = f"Case {case_id[:8].upper()}"

    case_dir = os.path.join(settings.raw_data_path, case_id)
    os.makedirs(case_dir, exist_ok=True)

    accepted = []
    rejected = []
    saved_files = []

    for file in files:
        filename = file.filename or "unknown"
        ext = os.path.splitext(filename)[1].lower()

        if ext not in ALLOWED_EXTENSIONS:
            rejected.append(filename)
            continue

        # Read and check size
        content = await file.read()
        if len(content) > settings.max_file_size_bytes:
            rejected.append(f"{filename} (too large)")
            continue

        # Save file
        save_path = os.path.join(case_dir, filename)
        with open(save_path, "wb") as f:
            f.write(content)
        accepted.append(filename)
        saved_files.append((filename, save_path))

    if not accepted:
        raise HTTPException(400, "No valid files uploaded.")

    # Register case in DB
    sqlite_repo.upsert_case(
        case_id=case_id,
        name=case_name,
        status="parsing",
        created_at=datetime.now(timezone.utc).isoformat()
    )
    _processing_status[case_id] = {"status": "parsing", "message": "Parsing documents..."}

    # Start background processing thread
    thread = threading.Thread(
        target=_process_case,
        args=(case_id, saved_files),
        daemon=True
    )
    thread.start()

    return UploadResponse(
        case_id=case_id,
        accepted_files=accepted,
        rejected_files=rejected
    )


def _process_case(case_id: str, files: list[tuple[str, str]]):
    """Background processing pipeline: parse → chunk → embed → index → analyze."""
    try:
        all_chunks = []

        # ── PARSING ──────────────────────────────────────────────────────────
        _set_status(case_id, "parsing", "Parsing documents...")
        for filename, filepath in files:
            doc_id = new_uuid()
            ext = os.path.splitext(filepath)[1].lower()
            doc_type = document_parser.guess_doc_type(filename)

            pages = document_parser.parse_file(filepath)
            pages = text_cleaner.clean_pages(pages)
            document_parser.cache_parsed(settings.processed_data_path, case_id, doc_id, pages)

            page_count = len(pages)
            sqlite_repo.insert_document(doc_id, case_id, filename, doc_type, page_count)

            # ── CHUNKING ─────────────────────────────────────────────────────
            _set_status(case_id, "chunking", f"Chunking {filename}...")
            doc_chunks = chunker.chunk_document(doc_id, case_id, filename, doc_type, pages)

            for chunk in doc_chunks:
                sqlite_repo.insert_chunk(
                    chunk_id=chunk["chunk_id"],
                    doc_id=chunk["doc_id"],
                    case_id=chunk["case_id"],
                    chunk_index=chunk["chunk_index"],
                    page=chunk["page"],
                    text=chunk["text"],
                    char_start=chunk.get("char_start", 0),
                    char_end=chunk.get("char_end", 0)
                )
            sqlite_repo.update_document_chunk_count(doc_id, len(doc_chunks))
            all_chunks.extend(doc_chunks)

            # ── ENTITY EXTRACTION ────────────────────────────────────────────
            _set_status(case_id, "indexing", f"Extracting entities from {filename}...")
            full_text = "\n".join(t for _, t in pages)
            try:
                entity_extractor.extract_and_store_entities(case_id, doc_id, filename, full_text)
            except Exception as e:
                logger.warning(f"Entity extraction failed for {filename}: {e}")

        # ── EMBEDDING ─────────────────────────────────────────────────────────
        _set_status(case_id, "embedding", "Generating embeddings...")
        texts = [c["text"] for c in all_chunks]
        embeddings = embedder.embed(texts)

        # ── VECTOR STORE ──────────────────────────────────────────────────────
        _set_status(case_id, "indexing", "Indexing into vector store...")
        chunk_ids = [c["chunk_id"] for c in all_chunks]
        documents_text = texts
        metadatas = [{
            "case_id": c["case_id"],
            "doc_id": c["doc_id"],
            "filename": c["filename"],
            "doc_type": c["doc_type"],
            "page": c["page"],
            "chunk_index": c["chunk_index"],
        } for c in all_chunks]

        chroma_repo.add_chunks(case_id, chunk_ids, embeddings, documents_text, metadatas)

        # ── DETECTIVE ANALYSIS ────────────────────────────────────────────────
        _set_status(case_id, "indexing", "Detecting contradictions...")
        try:
            contradiction_engine.detect_and_store_contradictions(case_id)
        except Exception as e:
            logger.warning(f"Contradiction detection failed: {e}")

        _set_status(case_id, "indexing", "Building timeline...")
        try:
            timeline_engine.build_and_store_timeline(case_id)
        except Exception as e:
            logger.warning(f"Timeline building failed: {e}")

        _set_status(case_id, "indexing", "Scoring suspects...")
        try:
            suspect_scorer.score_and_store_suspects(case_id)
        except Exception as e:
            logger.warning(f"Suspect scoring failed: {e}")

        # ── READY ─────────────────────────────────────────────────────────────
        _set_status(case_id, "ready", "Case file ready for investigation.")
        sqlite_repo.update_case_status(case_id, "ready")
        logger.info(f"Case {case_id} processing complete.")

    except Exception as e:
        logger.error(f"Case {case_id} processing failed: {e}\n{traceback.format_exc()}")
        _set_status(case_id, "error", str(e))
        sqlite_repo.update_case_status(case_id, "error")


def _set_status(case_id: str, status: str, message: str):
    _processing_status[case_id] = {"status": status, "message": message}
