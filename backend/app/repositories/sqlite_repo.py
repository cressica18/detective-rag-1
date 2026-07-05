"""SQLite repository — all database access."""
import sqlite3
import json
import os
from typing import Optional
from app.config import settings
from app.models.db_models import CREATE_TABLES_SQL


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    os.makedirs(os.path.dirname(settings.database_path) if os.path.dirname(settings.database_path) else ".", exist_ok=True)
    with get_connection() as conn:
        conn.executescript(CREATE_TABLES_SQL)
        conn.commit()


# ── Cases ──────────────────────────────────────────────────────────────────────

def upsert_case(case_id: str, name: str, status: str, created_at: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO cases (case_id, name, created_at, status) VALUES (?,?,?,?)",
            (case_id, name, created_at, status)
        )
        conn.commit()


def update_case_status(case_id: str, status: str):
    with get_connection() as conn:
        conn.execute("UPDATE cases SET status=? WHERE case_id=?", (status, case_id))
        conn.commit()


def get_case(case_id: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
        return dict(row) if row else None


# ── Documents ──────────────────────────────────────────────────────────────────

def insert_document(doc_id: str, case_id: str, filename: str, doc_type: str, page_count: int):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO documents (doc_id, case_id, filename, doc_type, page_count) VALUES (?,?,?,?,?)",
            (doc_id, case_id, filename, doc_type, page_count)
        )
        conn.commit()


def update_document_chunk_count(doc_id: str, chunk_count: int):
    with get_connection() as conn:
        conn.execute("UPDATE documents SET chunk_count=? WHERE doc_id=?", (chunk_count, doc_id))
        conn.commit()


def get_documents(case_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM documents WHERE case_id=?", (case_id,)).fetchall()
        return [dict(r) for r in rows]


def get_document(doc_id: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM documents WHERE doc_id=?", (doc_id,)).fetchone()
        return dict(row) if row else None


# ── Chunks ─────────────────────────────────────────────────────────────────────

def insert_chunk(chunk_id: str, doc_id: str, case_id: str, chunk_index: int, page: int, text: str, char_start: int = 0, char_end: int = 0):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO chunks (chunk_id, doc_id, case_id, chunk_index, page, text, char_start, char_end) VALUES (?,?,?,?,?,?,?,?)",
            (chunk_id, doc_id, case_id, chunk_index, page, text, char_start, char_end)
        )
        conn.commit()


def get_chunks_for_doc(doc_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM chunks WHERE doc_id=? ORDER BY chunk_index", (doc_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_chunk(chunk_id: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM chunks WHERE chunk_id=?", (chunk_id,)).fetchone()
        return dict(row) if row else None


# ── Entities ───────────────────────────────────────────────────────────────────

def insert_entity(case_id: str, doc_id: str, entity_type: str, value: str, context_snippet: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO entities (case_id, doc_id, entity_type, value, context_snippet) VALUES (?,?,?,?,?)",
            (case_id, doc_id, entity_type, value, context_snippet)
        )
        conn.commit()


def get_entities(case_id: str, entity_type: Optional[str] = None) -> list[dict]:
    with get_connection() as conn:
        if entity_type:
            rows = conn.execute(
                "SELECT * FROM entities WHERE case_id=? AND entity_type=?", (case_id, entity_type)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM entities WHERE case_id=?", (case_id,)).fetchall()
        return [dict(r) for r in rows]


def delete_entities_for_case(case_id: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM entities WHERE case_id=?", (case_id,))
        conn.commit()


# ── Contradictions ─────────────────────────────────────────────────────────────

def insert_contradiction(id: str, case_id: str, claim_a: str, claim_a_doc_id: str,
                          claim_b: str, claim_b_doc_id: str, explanation: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO contradictions (id, case_id, claim_a, claim_a_doc_id, claim_b, claim_b_doc_id, explanation) VALUES (?,?,?,?,?,?,?)",
            (id, case_id, claim_a, claim_a_doc_id, claim_b, claim_b_doc_id, explanation)
        )
        conn.commit()


def get_contradictions(case_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM contradictions WHERE case_id=?", (case_id,)).fetchall()
        return [dict(r) for r in rows]


def delete_contradictions_for_case(case_id: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM contradictions WHERE case_id=?", (case_id,))
        conn.commit()


# ── Timeline Events ────────────────────────────────────────────────────────────

def insert_timeline_event(event_id: str, case_id: str, timestamp: str, description: str,
                            source_doc_ids: list[str], is_contradicted: bool):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO timeline_events (event_id, case_id, timestamp, description, source_doc_ids, is_contradicted) VALUES (?,?,?,?,?,?)",
            (event_id, case_id, timestamp, description, json.dumps(source_doc_ids), int(is_contradicted))
        )
        conn.commit()


def get_timeline_events(case_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM timeline_events WHERE case_id=? ORDER BY timestamp", (case_id,)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["source_doc_ids"] = json.loads(d["source_doc_ids"])
            d["is_contradicted"] = bool(d["is_contradicted"])
            result.append(d)
        return result


def delete_timeline_for_case(case_id: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM timeline_events WHERE case_id=?", (case_id,))
        conn.commit()


# ── Suspects ───────────────────────────────────────────────────────────────────

def upsert_suspect(name: str, case_id: str, role: str, opportunity_score: float, motive_score: float,
                    contradiction_count: int, evidence_strength: float, total_score: float, motive_summary: str):
    with get_connection() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO suspects 
               (name, case_id, role, opportunity_score, motive_score, contradiction_count, evidence_strength, total_score, motive_summary)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (name, case_id, role, opportunity_score, motive_score, contradiction_count, evidence_strength, total_score, motive_summary)
        )
        conn.commit()


def get_suspects(case_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM suspects WHERE case_id=? ORDER BY total_score DESC", (case_id,)).fetchall()
        return [dict(r) for r in rows]


def delete_suspects_for_case(case_id: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM suspects WHERE case_id=?", (case_id,))
        conn.commit()
