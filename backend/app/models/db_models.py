"""SQLite schema definitions and initialization."""

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    name TEXT,
    created_at TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    case_id TEXT,
    filename TEXT,
    doc_type TEXT,
    page_count INTEGER,
    chunk_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT,
    case_id TEXT,
    chunk_index INTEGER,
    page INTEGER,
    text TEXT,
    char_start INTEGER DEFAULT 0,
    char_end INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT,
    doc_id TEXT,
    entity_type TEXT,
    value TEXT,
    context_snippet TEXT
);

CREATE TABLE IF NOT EXISTS contradictions (
    id TEXT PRIMARY KEY,
    case_id TEXT,
    claim_a TEXT,
    claim_a_doc_id TEXT,
    claim_b TEXT,
    claim_b_doc_id TEXT,
    explanation TEXT
);

CREATE TABLE IF NOT EXISTS timeline_events (
    event_id TEXT PRIMARY KEY,
    case_id TEXT,
    timestamp TEXT,
    description TEXT,
    source_doc_ids TEXT,
    is_contradicted INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS suspects (
    name TEXT,
    case_id TEXT,
    role TEXT DEFAULT 'unknown',
    opportunity_score REAL DEFAULT 0,
    motive_score REAL DEFAULT 0,
    contradiction_count INTEGER DEFAULT 0,
    evidence_strength REAL DEFAULT 0,
    total_score REAL DEFAULT 0,
    motive_summary TEXT DEFAULT '',
    PRIMARY KEY (name, case_id)
);
"""
