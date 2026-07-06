#!/usr/bin/env python3
"""
Seed script: loads all sample case documents into ChromaDB + SQLite,
then pre-populates suspects/timeline/contradictions.
Run from backend/ directory: python3 seed_case.py
"""
import os
import sys
import sqlite3
import uuid
import json

# Ensure backend app module path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CASE_ID = "riverside_case"
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_case", "riverside_museum_murder")
DB_PATH = "data/detective.db"
CHROMA_PATH = "data/chroma"
RAW_PATH = "data/raw"
PROCESSED_PATH = "data/processed"

def stable_id(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, "|".join(str(p) for p in parts)))

def reset_case(conn):
    cur = conn.cursor()
    for table in ["chunks", "documents", "entities", "contradictions", "timeline_events", "suspects"]:
        cur.execute(f"DELETE FROM {table} WHERE case_id=?", (CASE_ID,))
    cur.execute("DELETE FROM cases WHERE case_id=?", (CASE_ID,))
    conn.commit()
    print("  DB reset.")

def seed_documents(conn, reset: bool):
    """Parse all sample docs, chunk them, embed, store in Chroma + SQLite, then run analysis chain.
    Resumable: skips entity extraction for documents that already have stored entities,
    so re-running after a quota interruption doesn't re-burn LLM calls on already-processed docs.
    """
    import time
    from app.services import document_parser, text_cleaner, chunker, embedder
    from app.services import entity_extractor, contradiction_engine, timeline_engine, suspect_scorer
    from app.services.llm_client import QuotaExceededError
    from app.repositories import sqlite_repo, chroma_repo
    from datetime import datetime, timezone

    sqlite_repo.upsert_case(
        case_id=CASE_ID,
        name="The Riverside Museum Murder",
        status="parsing",
        created_at=datetime.now(timezone.utc).isoformat()
    )

    existing_entity_doc_ids = set()
    if not reset:
        existing_entity_doc_ids = {e["doc_id"] for e in sqlite_repo.get_entities(CASE_ID)}

    all_chunks = []
    files = sorted(os.listdir(SAMPLE_DIR))
    print(f"  Found {len(files)} sample files.")

    for fname in files:
        if not fname.endswith(".txt"):
            continue

        fpath = os.path.join(SAMPLE_DIR, fname)
        doc_id = stable_id(CASE_ID, fname)
        doc_type = document_parser.guess_doc_type(fname)

        pages = document_parser.parse_file(fpath)
        pages = text_cleaner.clean_pages(pages)
        document_parser.cache_parsed(PROCESSED_PATH, CASE_ID, doc_id, pages)

        page_count = len(pages)
        sqlite_repo.insert_document(doc_id, CASE_ID, fname, doc_type, page_count)

        doc_chunks = chunker.chunk_document(doc_id, CASE_ID, fname, doc_type, pages)
        for ch in doc_chunks:
            sqlite_repo.insert_chunk(
                chunk_id=ch["chunk_id"], doc_id=ch["doc_id"], case_id=ch["case_id"],
                chunk_index=ch["chunk_index"], page=ch["page"], text=ch["text"],
                char_start=ch.get("char_start", 0), char_end=ch.get("char_end", 0)
            )
        sqlite_repo.update_document_chunk_count(doc_id, len(doc_chunks))
        all_chunks.extend(doc_chunks)
        print(f"    {fname}: {len(doc_chunks)} chunks")

        if doc_id in existing_entity_doc_ids:
            print(f"    Entities already stored for {fname}, skipping extraction (resume mode).")
            continue

        print(f"    Extracting entities from {fname}...")
        full_text = "\n".join(t for _, t in pages)
        time.sleep(6)
        try:
            entity_extractor.extract_and_store_entities(CASE_ID, doc_id, fname, full_text)
        except QuotaExceededError:
            print(f"    Quota hit on {fname}, backing off 45s and retrying once...")
            time.sleep(45)
            try:
                entity_extractor.extract_and_store_entities(CASE_ID, doc_id, fname, full_text)
            except Exception as e2:
                print(f"    ERROR extracting entities from {fname} (after retry): {e2}")
        except Exception as e:
            print(f"    ERROR extracting entities from {fname}: {e}")

    print(f"  Total chunks: {len(all_chunks)}, embedding...")
    texts = [c["text"] for c in all_chunks]
    embeddings = embedder.embed(texts)

    chunk_ids = [c["chunk_id"] for c in all_chunks]
    metadatas = [{
        "case_id": c["case_id"], "doc_id": c["doc_id"], "filename": c["filename"],
        "doc_type": c["doc_type"], "page": c["page"], "chunk_index": c["chunk_index"],
    } for c in all_chunks]

    chroma_repo.add_chunks(CASE_ID, chunk_ids, embeddings, texts, metadatas)
    print(f"  ChromaDB indexed: {len(all_chunks)} chunks.")

    print("  Detecting contradictions...")
    try:
        time.sleep(6)
        contradiction_engine.detect_and_store_contradictions(CASE_ID)
    except Exception as e:
        print(f"  ERROR detecting contradictions: {e}")

    print("  Building timeline...")
    try:
        time.sleep(6)
        timeline_engine.build_and_store_timeline(CASE_ID)
    except Exception as e:
        print(f"  ERROR building timeline: {e}")

    print("  Scoring suspects...")
    try:
        time.sleep(6)
        suspect_scorer.score_and_store_suspects(CASE_ID)
    except Exception as e:
        print(f"  ERROR scoring suspects: {e}")

    sqlite_repo.update_case_status(CASE_ID, "ready")


def main():
    print("=== DetectiveRAG Case Seeder ===")
    print(f"Case ID: {CASE_ID}")

    reset = "--reset" in sys.argv
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if reset:
        print("\n[1] Resetting case data (--reset passed)...")
        reset_case(conn)
    else:
        print("\n[1] Resume mode: keeping existing documents/entities, only filling gaps.")
        print("    (pass --reset to wipe everything and start over)")

    print("\n[2] Loading and indexing documents...")
    try:
        seed_documents(conn, reset)
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

    conn.close()
    print("\n=== Seeding complete ===")
    print("Case 'riverside_case' is ready. Start backend and upload nothing — just navigate to the dashboard.")


if __name__ == "__main__":
    main()