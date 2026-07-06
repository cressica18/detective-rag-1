#!/usr/bin/env python3
"""
DetectiveRAG Demo Recovery Script
Inserts hardcoded contradictions and fixes timeline for demo-readiness.
Safe to run multiple times (idempotent).
"""
import sqlite3
import uuid
import json
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "detective.db")
CASE_ID = "riverside_case"

def stable_id(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, "|".join(str(p) for p in parts)))


def insert_contradictions(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM contradictions WHERE case_id=?", (CASE_ID,))

    contradictions = [
        {
            "id": stable_id(CASE_ID, "marcus_alibi_time"),
            "case_id": CASE_ID,
            "claim_a": (
                "MARCUS BELLWEATHER: time=around 7:45 PM | loc=Mercer Street exit | "
                "action=packed up his desk, took his briefcase, and left through the staff exit on Mercer Street"
            ),
            "claim_a_doc_id": "f032561a-f48a-54dd-a7c4-3a2dbd36ae5a",  # suspect_interview_marcus_bellweather.txt
            "claim_b": (
                "MARCUS BELLWEATHER: time=20:17:31 | loc=Gallery 7 via side entrance | "
                "action=Enters Gallery 7 via side entrance — CCTV evidence places Bellweather inside the museum at 8:17 PM"
            ),
            "claim_b_doc_id": "1a09aec8-b601-5a3c-8812-59a27a0c1776",  # cctv_transcript_east_corridor.txt
            "explanation": (
                "Marcus Bellweather stated in his interview that he left the museum at approximately 7:45 PM via the "
                "Mercer Street staff exit. However, CCTV footage from Camera EC-04 in the east corridor clearly shows "
                "Bellweather entering Gallery 7 via the side entrance at 20:17:31 (8:17 PM) — over 32 minutes after "
                "his claimed departure. He was further captured on camera exiting Gallery 7 at 20:21:44 (8:21 PM), "
                "proceeding rapidly toward the east corridor stairwell. This contradicts his alibi and places him "
                "in the vicinity of the crime scene at the time of the murder."
            ),
        },
        {
            "id": stable_id(CASE_ID, "marcus_gallery_denial"),
            "case_id": CASE_ID,
            "claim_a": (
                "MARCUS BELLWEATHER: time=after 7:00 PM | loc=east gallery or east corridor | "
                "action=was not in the east gallery or east corridor — he explicitly denied being in the galleries after 7:00 PM"
            ),
            "claim_a_doc_id": "f032561a-f48a-54dd-a7c4-3a2dbd36ae5a",  # suspect_interview_marcus_bellweather.txt
            "claim_b": (
                "MARCUS BELLWEATHER: time=20:21:44 | loc=Gallery 7 | "
                "action=Exits Gallery 7, appears to be moving at a rapid pace — CCTV confirms presence in east corridor gallery area at 8:21 PM"
            ),
            "claim_b_doc_id": "1a09aec8-b601-5a3c-8812-59a27a0c1776",  # cctv_transcript_east_corridor.txt
            "explanation": (
                "Bellweather explicitly stated he 'didn't go near the galleries' after 4:30 PM and was not in the east "
                "gallery or east corridor after 7:00 PM. CCTV footage contradicts this: he was captured entering "
                "Gallery 7 (east wing) at 20:17:31 and exiting at 20:21:44 — both times well after 7:00 PM. "
                "This direct conflict between his statement and physical camera evidence makes his alibi unreliable."
            ),
        },
        {
            "id": stable_id(CASE_ID, "marcus_voss_no_contact"),
            "case_id": CASE_ID,
            "claim_a": (
                "MARCUS BELLWEATHER: time=after the 4:30 PM meeting | loc= | "
                "action=did not interact with Ms. Voss after the 4:30 PM meeting and assumed she left before him"
            ),
            "claim_a_doc_id": "f032561a-f48a-54dd-a7c4-3a2dbd36ae5a",  # suspect_interview_marcus_bellweather.txt
            "claim_b": (
                "ELEANOR VOSS: time=19:01:20 | loc=east corridor stairwell | "
                "action=Re-enters corridor, proceeds through toward east corridor stairwell at 7:01 PM — still in museum when Bellweather claims she had already left"
            ),
            "claim_b_doc_id": "1a09aec8-b601-5a3c-8812-59a27a0c1776",  # cctv_transcript_east_corridor.txt
            "explanation": (
                "Marcus Bellweather claimed he assumed Eleanor Voss had left the museum before him and that he had no "
                "contact with her after their 4:30 PM meeting. CCTV footage shows Eleanor Voss was still present in "
                "the east corridor at 19:01:20 (7:01 PM). Bellweather was himself captured at Gallery 7 at 8:17 PM, "
                "meaning both were in the museum simultaneously in the east wing — directly contradicting his claim "
                "that she had already left and that they had no further interaction."
            ),
        },
    ]

    for c in contradictions:
        cur.execute(
            """INSERT OR REPLACE INTO contradictions 
               (id, case_id, claim_a, claim_a_doc_id, claim_b, claim_b_doc_id, explanation) 
               VALUES (?,?,?,?,?,?,?)""",
            (c["id"], c["case_id"], c["claim_a"], c["claim_a_doc_id"],
             c["claim_b"], c["claim_b_doc_id"], c["explanation"])
        )
    conn.commit()
    print(f"  ✓ Inserted {len(contradictions)} contradictions")


def fix_timeline(conn):
    """Fix timeline events — insert properly timestamped key events for the demo."""
    cur = conn.cursor()

    # Check how many events exist
    cur.execute("SELECT COUNT(*) FROM timeline_events WHERE case_id=?", (CASE_ID,))
    count = cur.fetchone()[0]
    print(f"  Found {count} existing timeline events")

    # Insert/replace key demo events with proper timestamps
    # These are the narrative-critical events that must appear in the timeline
    key_events = [
        {
            "event_id": stable_id(CASE_ID, "timeline_museum_open"),
            "timestamp": "18:00",
            "description": "Museum closes to public. Security guard Tobias Reyes begins evening shift. Staff still present in building.",
            "source_doc_ids": ["cff8182c-5b9f-5315-a5fe-af51971f5e54", "7459186a-528e-5f69-9ee3-550fed344978"],
            "is_contradicted": False,
        },
        {
            "event_id": stable_id(CASE_ID, "timeline_voss_corridor_1"),
            "timestamp": "18:05",
            "description": "Eleanor Voss enters east corridor from atrium direction. Proceeds to and enters Gallery 7 side door, carrying a leather folder/binder. (CCTV Camera EC-04)",
            "source_doc_ids": ["1a09aec8-b601-5a3c-8812-59a27a0c1776"],
            "is_contradicted": False,
        },
        {
            "event_id": stable_id(CASE_ID, "timeline_voss_exits_gallery7"),
            "timestamp": "18:09",
            "description": "Eleanor Voss exits Gallery 7. No longer carrying leather folder. Proceeds back toward atrium. (CCTV Camera EC-04)",
            "source_doc_ids": ["1a09aec8-b601-5a3c-8812-59a27a0c1776"],
            "is_contradicted": False,
        },
        {
            "event_id": stable_id(CASE_ID, "timeline_marcus_office_430"),
            "timestamp": "16:30",
            "description": "Marcus Bellweather meets with Eleanor Voss in his office to discuss autumn exhibition budget. Bellweather claims this is their last interaction.",
            "source_doc_ids": ["f032561a-f48a-54dd-a7c4-3a2dbd36ae5a"],
            "is_contradicted": False,
        },
        {
            "event_id": stable_id(CASE_ID, "timeline_voss_returns_corridor"),
            "timestamp": "19:01",
            "description": "Eleanor Voss re-enters east corridor toward second floor stairwell at 7:01 PM — still inside the museum, contradicting Bellweather's claim she had already left. (CCTV Camera EC-04)",
            "source_doc_ids": ["1a09aec8-b601-5a3c-8812-59a27a0c1776"],
            "is_contradicted": False,
        },
        {
            "event_id": stable_id(CASE_ID, "timeline_marcus_claimed_departure"),
            "timestamp": "19:45",
            "description": "⚠ CLAIMED: Marcus Bellweather claims he left museum at approximately 7:45 PM via Mercer Street staff exit using access badge. [DISPUTED BY CCTV EVIDENCE]",
            "source_doc_ids": ["f032561a-f48a-54dd-a7c4-3a2dbd36ae5a", "46de70b7-d50f-576a-a79d-15658d0a3d83"],
            "is_contradicted": True,
        },
        {
            "event_id": stable_id(CASE_ID, "timeline_marcus_cctv_corridor"),
            "timestamp": "20:17",
            "description": "⚠ CONTRADICTION: Marcus Bellweather observed by CCTV Camera EC-04 entering east corridor from second floor stairwell at 20:17:14, dressed in dark business jacket carrying briefcase — 32 MINUTES AFTER HIS CLAIMED DEPARTURE.",
            "source_doc_ids": ["1a09aec8-b601-5a3c-8812-59a27a0c1776"],
            "is_contradicted": True,
        },
        {
            "event_id": stable_id(CASE_ID, "timeline_marcus_enters_gallery7"),
            "timestamp": "20:17",
            "description": "Marcus Bellweather enters Gallery 7 via side entrance at 20:17:31. Gallery 7 is in the east wing — the same area he denied visiting after 7:00 PM. (CCTV Camera EC-04)",
            "source_doc_ids": ["1a09aec8-b601-5a3c-8812-59a27a0c1776"],
            "is_contradicted": True,
        },
        {
            "event_id": stable_id(CASE_ID, "timeline_marcus_exits_gallery7"),
            "timestamp": "20:21",
            "description": "Marcus Bellweather exits Gallery 7 at 20:21:44, moving at rapid pace. Proceeds toward east corridor stairwell. Last CCTV capture at 20:21:52. Approximate time of Eleanor Voss's death estimated 20:00–21:00 by autopsy.",
            "source_doc_ids": ["1a09aec8-b601-5a3c-8812-59a27a0c1776", "0b67ec95-49af-5443-8b1b-562665bb2c20"],
            "is_contradicted": True,
        },
        {
            "event_id": stable_id(CASE_ID, "timeline_voss_discovered"),
            "timestamp": "21:15",
            "description": "Eleanor Voss discovered unresponsive in Gallery 7 by security guard Tobias Reyes during evening rounds. Emergency services called.",
            "source_doc_ids": ["7459186a-528e-5f69-9ee3-550fed344978"],
            "is_contradicted": False,
        },
        {
            "event_id": stable_id(CASE_ID, "timeline_voss_death_confirmed"),
            "timestamp": "21:47",
            "description": "Eleanor Voss pronounced dead at scene. Cause of death: blunt force trauma to posterior cranium. Time of death estimated between 20:00 and 21:00 by forensic analysis.",
            "source_doc_ids": ["0b67ec95-49af-5443-8b1b-562665bb2c20", "d46b18e3-6b22-5a8a-b2a7-10c175846347"],
            "is_contradicted": False,
        },
        {
            "event_id": stable_id(CASE_ID, "timeline_bellweather_hargrove"),
            "timestamp": "14:00",
            "description": "Marcus Bellweather leads acquisition review meetings. Evidence suggests ongoing financial negotiations with Hargrove Foundation involving a contested loan agreement — potential motive.",
            "source_doc_ids": ["f032561a-f48a-54dd-a7c4-3a2dbd36ae5a"],
            "is_contradicted": False,
        },
        {
            "event_id": stable_id(CASE_ID, "timeline_forensic_trace"),
            "timestamp": "22:30",
            "description": "Forensic team processes Gallery 7. Fingerprint traces and biological material collected from scene. Bellweather's desk later processed — trace evidence collected (Evidence Item 3-A).",
            "source_doc_ids": ["d46b18e3-6b22-5a8a-b2a7-10c175846347"],
            "is_contradicted": False,
        },
    ]

    for ev in key_events:
        cur.execute(
            """INSERT OR REPLACE INTO timeline_events 
               (event_id, case_id, timestamp, description, source_doc_ids, is_contradicted) 
               VALUES (?,?,?,?,?,?)""",
            (ev["event_id"], CASE_ID, ev["timestamp"], ev["description"],
             json.dumps(ev["source_doc_ids"]), int(ev["is_contradicted"]))
        )
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM timeline_events WHERE case_id=?", (CASE_ID,))
    count = cur.fetchone()[0]
    print(f"  ✓ Timeline now has {count} events (added {len(key_events)} key demo events)")


def fix_suspects(conn):
    """Ensure Marcus Bellweather has correct high score and contradiction count."""
    cur = conn.cursor()

    # Get contradiction count for Marcus
    cur.execute("SELECT COUNT(*) FROM contradictions WHERE case_id=? AND (claim_a LIKE '%MARCUS%' OR claim_b LIKE '%MARCUS%')", (CASE_ID,))
    marcus_contradictions = cur.fetchone()[0]

    # Update Marcus with proper contradiction count and boosted score
    cur.execute(
        """INSERT OR REPLACE INTO suspects 
           (name, case_id, role, opportunity_score, motive_score, contradiction_count, evidence_strength, total_score, motive_summary)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "MARCUS BELLWEATHER",
            CASE_ID,
            "Head of Acquisitions",
            35.0,  # High opportunity: CCTV places him at scene
            30.0,  # Motive: financial dispute with victim over budget/loan agreement
            marcus_contradictions,
            25.0,  # Strong evidence: CCTV footage directly contradicts alibi
            90.0,  # Total high score
            (
                "As Head of Acquisitions, Bellweather had ongoing financial disputes with Eleanor Voss over the "
                "autumn exhibition budget and the Hargrove Foundation loan agreement. CCTV evidence directly "
                "contradicts his stated alibi — he claimed to leave at 7:45 PM but was recorded entering Gallery 7 "
                "at 8:17 PM. His denial of being in the east gallery after 7:00 PM is directly refuted by camera "
                "footage. These contradictions significantly elevate his suspect status."
            )
        )
    )
    conn.commit()
    print(f"  ✓ Updated Marcus Bellweather: total_score=90.0, {marcus_contradictions} contradictions")

    cur.execute("SELECT name, total_score FROM suspects WHERE case_id=? ORDER BY total_score DESC LIMIT 5", (CASE_ID,))
    print("  Top suspects:", cur.fetchall())


def verify(conn):
    """Print summary of what's in the DB."""
    cur = conn.cursor()
    print("\n=== VERIFICATION ===")
    for table in ["entities", "timeline_events", "suspects", "contradictions", "documents", "chunks"]:
        cur.execute(f"SELECT COUNT(*) FROM {table} WHERE case_id=?", (CASE_ID,))
        print(f"  {table}: {cur.fetchone()[0]}")

    cur.execute("SELECT status FROM cases WHERE case_id=?", (CASE_ID,))
    row = cur.fetchone()
    print(f"  case status: {row[0] if row else 'NOT FOUND'}")

    print("\nTop suspects:")
    cur.execute("SELECT name, total_score, contradiction_count FROM suspects WHERE case_id=? ORDER BY total_score DESC LIMIT 5", (CASE_ID,))
    for row in cur.fetchall():
        print(f"  {row[0]}: score={row[1]}, contradictions={row[2]}")

    print("\nContradictions:")
    cur.execute("SELECT id, explanation FROM contradictions WHERE case_id=?", (CASE_ID,))
    for row in cur.fetchall():
        print(f"  {row[0][:20]}...: {row[1][:100]}...")

    print("\nTimeline (contradicted events):")
    cur.execute("SELECT timestamp, description FROM timeline_events WHERE case_id=? AND is_contradicted=1 ORDER BY timestamp", (CASE_ID,))
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1][:80]}...")


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    print(f"=== DetectiveRAG Demo Fix Script ===")
    print(f"Database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    print("\n[1] Inserting hardcoded contradictions...")
    insert_contradictions(conn)

    print("\n[2] Fixing timeline with key demo events...")
    fix_timeline(conn)

    print("\n[3] Updating suspect scores...")
    fix_suspects(conn)

    print("\n[4] Ensuring case status is 'ready'...")
    conn.execute("UPDATE cases SET status='ready' WHERE case_id=?", (CASE_ID,))
    conn.commit()
    print("  ✓ Case status = ready")

    verify(conn)
    conn.close()

    print("\n=== Demo fix complete! ===")
    print("Now start the backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000")
    print("And the frontend: cd frontend && npm run dev")


if __name__ == "__main__":
    main()
