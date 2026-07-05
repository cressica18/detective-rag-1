#!/usr/bin/env python3
"""
Seed script: loads all sample case documents into ChromaDB + SQLite,
then pre-populates suspects/timeline/contradictions without LLM.
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

def seed_documents(conn):
    """Parse all sample docs, chunk them, embed, store in Chroma + SQLite."""
    from app.services import document_parser, text_cleaner, chunker, embedder
    from app.repositories import sqlite_repo, chroma_repo
    from app.utils.ids import new_uuid
    from datetime import datetime, timezone

    sqlite_repo.upsert_case(
        case_id=CASE_ID,
        name="The Riverside Museum Murder",
        status="ready",
        created_at=datetime.now(timezone.utc).isoformat()
    )

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

def seed_entities(conn):
    """Insert key entities derived from reading the case documents."""
    cur = conn.cursor()
    doc_map = {}
    from app.services import document_parser
    for fname in os.listdir(SAMPLE_DIR):
        if fname.endswith(".txt"):
            doc_id = stable_id(CASE_ID, fname)
            doc_map[fname] = doc_id

    entities = [
        # People
        (CASE_ID, doc_map.get("suspect_interview_marcus_bellweather.txt",""), "person", "Marcus Bellweather", "Head of Acquisitions, Riverside Museum"),
        (CASE_ID, doc_map.get("witness_statement_lydia_ferro.txt",""), "person", "Lydia Ferro", "Restoration specialist, witness"),
        (CASE_ID, doc_map.get("suspect_interview_tobias_reyes.txt",""), "person", "Tobias Reyes", "Night security guard"),
        (CASE_ID, doc_map.get("autopsy_report_eleanor_voss.txt",""), "person", "Eleanor Voss", "Victim, Chief Curator"),
        (CASE_ID, doc_map.get("witness_statement_janitor.txt",""), "person", "Robert Mead", "Janitor, witness"),
        # Times
        (CASE_ID, doc_map.get("suspect_interview_marcus_bellweather.txt",""), "time", "7:45 PM", "Bellweather claims he left at 7:45 PM via Mercer Street exit"),
        (CASE_ID, doc_map.get("security_log_badge_swipes.txt",""), "time", "20:14", "Badge swipe: Bellweather, East Gallery stairwell access — 20:14:07"),
        (CASE_ID, doc_map.get("cctv_transcript_east_corridor.txt",""), "time", "20:17", "CCTV: Male figure matching Bellweather description enters east corridor at 20:17:22"),
        (CASE_ID, doc_map.get("autopsy_report_eleanor_voss.txt",""), "time", "20:00-21:00", "Estimated time of death: between 20:00 and 21:00"),
        (CASE_ID, doc_map.get("witness_statement_lydia_ferro.txt",""), "time", "8:15 PM", "Lydia claims she saw Bellweather leaving the building at 8:15 PM"),
        (CASE_ID, doc_map.get("cctv_transcript_east_corridor.txt",""), "time", "19:05", "Eleanor Voss enters east corridor at 19:05:40"),
        (CASE_ID, doc_map.get("witness_statement_janitor.txt",""), "time", "9:48 PM", "Robert Mead discovers body at 21:48"),
        # Locations
        (CASE_ID, doc_map.get("security_log_badge_swipes.txt",""), "location", "East Gallery", "Badge logs show Bellweather accessed east gallery stairwell at 20:14"),
        (CASE_ID, doc_map.get("forensic_report_scene.txt",""), "location", "Gallery 7", "Crime scene: Eleanor Voss found in Gallery 7"),
    ]

    for case_id, doc_id, etype, value, context in entities:
        if doc_id:
            cur.execute(
                "INSERT OR IGNORE INTO entities (case_id, doc_id, entity_type, value, context_snippet) VALUES (?,?,?,?,?)",
                (case_id, doc_id, etype, value, context)
            )
    conn.commit()
    print(f"  Inserted {len(entities)} entities.")

def seed_timeline(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM timeline_events WHERE case_id=?", (CASE_ID,))

    marcus_doc = stable_id(CASE_ID, "suspect_interview_marcus_bellweather.txt")
    security_doc = stable_id(CASE_ID, "security_log_badge_swipes.txt")
    cctv_doc = stable_id(CASE_ID, "cctv_transcript_east_corridor.txt")
    autopsy_doc = stable_id(CASE_ID, "autopsy_report_eleanor_voss.txt")
    lydia_doc = stable_id(CASE_ID, "witness_statement_lydia_ferro.txt")
    janitor_doc = stable_id(CASE_ID, "witness_statement_janitor.txt")
    forensic_doc = stable_id(CASE_ID, "forensic_report_scene.txt")

    events = [
        ("08:00", "Museum opens. Staff begin arriving. Eleanor Voss (Chief Curator) enters main entrance.", [security_doc], False),
        ("16:30", "Eleanor Voss visits Marcus Bellweather's office to discuss autumn exhibition budget.", [marcus_doc], False),
        ("19:05", "CCTV: Eleanor Voss enters east corridor from atrium direction, alone.", [cctv_doc], False),
        ("19:45", "Tobias Reyes begins evening security patrol. Signs in at security post.", [stable_id(CASE_ID, "suspect_interview_tobias_reyes.txt")], False),
        ("19:58", "Lydia Ferro exits restoration lab, takes south stairwell to ground floor.", [lydia_doc], False),
        ("20:00", "Estimated time of death window begins (forensic: 20:00-21:00).", [autopsy_doc], False),
        ("20:14", "Badge log: Bellweather badge swipes East Gallery stairwell access — CONTRADICTS his statement he left at 19:45.", [security_doc], True),
        ("20:17", "CCTV: Male figure matching Bellweather's build and clothing enters east corridor.", [cctv_doc], True),
        ("20:25", "CCTV: Figure and Voss seen together at Gallery 7 side entrance. Partially obscured.", [cctv_doc], False),
        ("20:45", "Bellweather claims he was home by 8:15 PM — CONTRADICTED by badge and CCTV evidence.", [marcus_doc, security_doc], True),
        ("21:05", "Lydia Ferro texts a friend: 'Just left the museum, horrible evening.'", [lydia_doc], False),
        ("21:48", "Janitor Robert Mead discovers Eleanor Voss's body in Gallery 7. Alerts security.", [janitor_doc], False),
        ("21:52", "Tobias Reyes calls 911. First responders dispatched.", [stable_id(CASE_ID, "police_report_001.txt")], False),
        ("22:10", "RPD arrives on scene. Gallery 7 sealed as crime scene.", [stable_id(CASE_ID, "police_report_001.txt")], False),
    ]

    for ts, desc, docs, contradicted in events:
        event_id = stable_id(CASE_ID, ts, desc[:20])
        cur.execute(
            "INSERT OR REPLACE INTO timeline_events (event_id, case_id, timestamp, description, source_doc_ids, is_contradicted) VALUES (?,?,?,?,?,?)",
            (event_id, CASE_ID, ts, desc, json.dumps(docs), 1 if contradicted else 0)
        )
    conn.commit()
    print(f"  Inserted {len(events)} timeline events.")

def seed_contradictions(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM contradictions WHERE case_id=?", (CASE_ID,))

    marcus_doc = stable_id(CASE_ID, "suspect_interview_marcus_bellweather.txt")
    security_doc = stable_id(CASE_ID, "security_log_badge_swipes.txt")
    cctv_doc = stable_id(CASE_ID, "cctv_transcript_east_corridor.txt")
    lydia_doc = stable_id(CASE_ID, "witness_statement_lydia_ferro.txt")

    contradictions = [
        (
            stable_id(CASE_ID, "contradiction_1"),
            "Marcus Bellweather states he left the museum via the Mercer Street staff exit at approximately 7:45 PM (19:45) and did not enter the east gallery or east corridor after 7:00 PM.",
            marcus_doc,
            "Electronic badge access log records Badge ID B-0017 (Bellweather, Marcus) activating the East Gallery Stairwell access point at 20:14:07, over 30 minutes after his claimed departure time.",
            security_doc,
            "Bellweather's sworn account of his departure time (19:45) is directly contradicted by the tamper-evident electronic access log showing his badge in the East Gallery at 20:14 — 29 minutes later than he claims to have left the building entirely."
        ),
        (
            stable_id(CASE_ID, "contradiction_2"),
            "Marcus Bellweather states he did not go near the galleries after 7:00 PM and went directly from his office to the Mercer Street exit.",
            marcus_doc,
            "CCTV Camera EC-04 (East Corridor, verified NTP timestamp) records a male figure matching Bellweather's described build, dark jacket, and briefcase entering the east corridor at 20:17:22, consistent with the badge access log.",
            cctv_doc,
            "Bellweather's claim of never approaching the east gallery is contradicted by CCTV footage showing a figure matching his description in the east corridor at 20:17, two minutes after his badge granted access to the east gallery stairwell."
        ),
        (
            stable_id(CASE_ID, "contradiction_3"),
            "Lydia Ferro's witness statement says she saw Marcus Bellweather in the main lobby at approximately 8:15 PM (20:15) collecting his coat from the cloakroom.",
            lydia_doc,
            "Badge log shows Bellweather's badge activating the East Gallery Stairwell at 20:14:07. The main lobby cloakroom and the East Gallery Stairwell are physically incompatible locations to occupy simultaneously.",
            security_doc,
            "Lydia Ferro's account places Bellweather in the main lobby at 20:15, while electronic logs place his badge in the East Gallery Stairwell at 20:14 — these locations are on opposite sides of the building, making both accounts simultaneously impossible."
        ),
    ]

    for cid, claim_a, doc_a, claim_b, doc_b, explanation in contradictions:
        cur.execute(
            "INSERT OR REPLACE INTO contradictions (id, case_id, claim_a, claim_a_doc_id, claim_b, claim_b_doc_id, explanation) VALUES (?,?,?,?,?,?,?)",
            (cid, CASE_ID, claim_a, doc_a, claim_b, doc_b, explanation)
        )
    conn.commit()
    print(f"  Inserted {len(contradictions)} contradictions.")

def seed_suspects(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM suspects WHERE case_id=?", (CASE_ID,))

    marcus_doc = stable_id(CASE_ID, "suspect_interview_marcus_bellweather.txt")

    suspects = [
        {
            "name": "Marcus Bellweather",
            "role": "Head of Acquisitions (Suspect)",
            "opportunity_score": 92.0,
            "motive_score": 78.0,
            "contradiction_count": 3,
            "evidence_strength": 85.0,
            "total_score": 86.5,
            "motive_summary": "Stood to benefit from Eleanor Voss's removal as Chief Curator due to ongoing conflict over the disputed Hargrove Foundation loan agreement and the autumn exhibition budget, which Voss was blocking. Financial records suggest Bellweather had personal stakes in the Hargrove deal."
        },
        {
            "name": "Tobias Reyes",
            "role": "Night Security Guard (Person of Interest)",
            "opportunity_score": 55.0,
            "motive_score": 20.0,
            "contradiction_count": 0,
            "evidence_strength": 15.0,
            "total_score": 30.0,
            "motive_summary": "On duty during the time of death, had keys and access to all areas. No established motive. Alibi is partially corroborated by sign-in logs, though a 45-minute gap in his patrol log remains unexplained."
        },
        {
            "name": "Lydia Ferro",
            "role": "Restoration Specialist (Witness)",
            "opportunity_score": 30.0,
            "motive_score": 15.0,
            "contradiction_count": 1,
            "evidence_strength": 10.0,
            "total_score": 19.0,
            "motive_summary": "Present in the museum until approximately 20:05. Witness statement contains a location inconsistency that places Bellweather in the wrong location at a critical time, which may indicate either honest mistake or deliberate misdirection."
        },
    ]

    for s in suspects:
        cur.execute(
            """INSERT OR REPLACE INTO suspects 
               (name, case_id, role, opportunity_score, motive_score, contradiction_count, evidence_strength, total_score, motive_summary)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (s["name"], CASE_ID, s["role"], s["opportunity_score"], s["motive_score"],
             s["contradiction_count"], s["evidence_strength"], s["total_score"], s["motive_summary"])
        )
    conn.commit()
    print(f"  Inserted {len(suspects)} suspects. Prime: Marcus Bellweather (86.5)")

def main():
    print("=== DetectiveRAG Case Seeder ===")
    print(f"Case ID: {CASE_ID}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    print("\n[1] Resetting case data...")
    reset_case(conn)

    print("\n[2] Loading and indexing documents (embedding with sentence-transformers)...")
    try:
        seed_documents(conn)
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

    print("\n[3] Seeding entities...")
    seed_entities(conn)

    print("\n[4] Seeding timeline events...")
    seed_timeline(conn)

    print("\n[5] Seeding contradictions...")
    seed_contradictions(conn)

    print("\n[6] Seeding suspect scores...")
    seed_suspects(conn)

    conn.close()
    print("\n=== Seeding complete ===")
    print("Case 'riverside_case' is ready. Start backend and upload nothing — just navigate to the dashboard.")

if __name__ == "__main__":
    main()
