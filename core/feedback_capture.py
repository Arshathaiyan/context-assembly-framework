import json

def save_feedback(conn, instruction_id: int, user_id: int, rating: int, tags: list, flagged: bool, version_number: int = None, manual_edits: bool = False):
    """
    Save user feedback for a given instruction.
    Arguments:
        conn            - SQLite connection
        instruction_id  - ID of the instruction being rated
        user_id         - ID of the user submitting feedback
        rating          - Numeric rating (e.g. 1–5)
        tags            - List of tag strings (e.g. ['unclear', 'verbose'])
        flagged         - Boolean, True if the output is flagged for review
        version_number  - Version number rated
        manual_edits    - Boolean, True if user made manual edits in this iteration
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instruction_id INTEGER NOT NULL,
            user_id INTEGER,
            rating INTEGER,
            tags TEXT,
            flagged INTEGER DEFAULT 0,
            version_number INTEGER,
            manual_edits INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (instruction_id) REFERENCES instructions(id)
        )
    """)
    conn.execute(
        "INSERT INTO feedback (instruction_id, user_id, rating, tags, flagged, version_number, manual_edits) VALUES (?,?,?,?,?,?,?)",
        (instruction_id, user_id, rating, json.dumps(tags), int(flagged), version_number, int(manual_edits)),
    )
    conn.commit()


def get_feedback(conn, instruction_id: int, version_number: int = None) -> list:
    """Return all feedback rows for a given instruction, optionally filtered by version."""
    if version_number is not None:
        rows = conn.execute(
            "SELECT * FROM feedback WHERE instruction_id=? AND version_number=? ORDER BY created_at DESC",
            (instruction_id, version_number),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM feedback WHERE instruction_id=? ORDER BY created_at DESC",
            (instruction_id,),
        ).fetchall()
    return [dict(r) for r in rows]