def create_version(conn, instruction_id, content, change_description="", context_id=None):
    cur = conn.execute(
        "SELECT MAX(version_number) FROM versions WHERE instruction_id=?", (instruction_id,)
    )
    last = cur.fetchone()[0] or 0
    new_version = last + 1
    conn.execute(
        "INSERT INTO versions (instruction_id, version_number, content, change_description, context_id) VALUES (?,?,?,?,?)",
        (instruction_id, new_version, content, change_description, context_id),
    )
    conn.commit()
    return new_version

def get_version_history(conn, instruction_id):
    return conn.execute(
        "SELECT version_number, content, change_description, context_id, created_at FROM versions WHERE instruction_id=? ORDER BY version_number",
        (instruction_id,),
    ).fetchall()