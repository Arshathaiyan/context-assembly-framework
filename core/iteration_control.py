import json
from datetime import datetime

def save_context(conn, answers_dict: dict) -> int:
    """
    Serialize the answers dictionary as a JSON string and store it in contexts.
    Returns the auto-generated context ID.
    """
    answers_json = json.dumps(answers_dict)
    cur = conn.execute(
        "INSERT INTO contexts (answers) VALUES (?)",
        (answers_json,)
    )
    conn.commit()
    return cur.lastrowid

def get_context_answers(conn, context_id: int) -> dict:
    """
    Retrieve and parse the answers dictionary from contexts.
    Returns an empty dict if the context_id is None or not found.
    """
    if not context_id:
        return {}
    row = conn.execute(
        "SELECT answers FROM contexts WHERE id = ?",
        (context_id,)
    ).fetchone()
    if row:
        try:
            return json.loads(row[0])
        except Exception:
            return {}
    return {}

def create_iteration_link(conn, parent_iid: int, child_iid: int, parent_ver: int, child_ver: int, change_type: str, notes: str = ""):
    """
    Logs an iteration/transition link between versions.
    """
    conn.execute(
        "INSERT INTO iteration_links (parent_instruction_id, child_instruction_id, parent_version, child_version, change_type, notes) VALUES (?,?,?,?,?,?)",
        (parent_iid, child_iid, parent_ver, child_ver, change_type, notes)
    )
    conn.commit()

def get_audit_trail(conn, instruction_id: int) -> list:
    """
    Generates a unified chronological audit trail of all versions, feedback submissions,
    and transition links for a given instruction.
    """
    events = []

    # 1. Fetch all versions
    versions = conn.execute(
        "SELECT version_number, content, change_description, context_id, created_at FROM versions WHERE instruction_id = ?",
        (instruction_id,)
    ).fetchall()
    for v in versions:
        events.append({
            "type": "version",
            "timestamp": v["created_at"],
            "version_number": v["version_number"],
            "content": v["content"],
            "change_description": v["change_description"],
            "context_id": v["context_id"],
        })

    # 2. Fetch all feedback
    feedbacks = conn.execute(
        "SELECT rating, tags, manual_edits, version_number, created_at FROM feedback WHERE instruction_id = ?",
        (instruction_id,)
    ).fetchall()
    for f in feedbacks:
        events.append({
            "type": "feedback",
            "timestamp": f["created_at"],
            "rating": f["rating"],
            "tags": json.loads(f["tags"]) if f["tags"] else [],
            "manual_edits": bool(f["manual_edits"]),
            "version_number": f["version_number"],
        })

    # 3. Fetch iteration links
    links = conn.execute(
        "SELECT parent_version, child_version, change_type, notes, created_at FROM iteration_links WHERE parent_instruction_id = ?",
        (instruction_id,)
    ).fetchall()
    for l in links:
        events.append({
            "type": "transition",
            "timestamp": l["created_at"],
            "parent_version": l["parent_version"],
            "child_version": l["child_version"],
            "change_type": l["change_type"],
            "notes": l["notes"],
        })

    # Sort events by timestamp (chronologically)
    def parse_time(ts):
        try:
            return datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.min

    events.sort(key=lambda e: parse_time(e["timestamp"]))
    return events
