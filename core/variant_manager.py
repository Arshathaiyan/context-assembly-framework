def create_variant(conn, parent_instruction_id, content):
    conn.execute(
        "INSERT INTO variants (parent_instruction_id, content) VALUES (?,?)",
        (parent_instruction_id, content),
    )
    conn.commit()

def get_variants(conn, parent_instruction_id):
    return conn.execute(
        "SELECT id, content, created_at FROM variants WHERE parent_instruction_id=?",
        (parent_instruction_id,),
    ).fetchall()