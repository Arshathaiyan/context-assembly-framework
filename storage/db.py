import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "caf.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS contexts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            answers TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS instructions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            context_id INTEGER,
            business_name TEXT,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (context_id) REFERENCES contexts(id)
        );

        CREATE TABLE IF NOT EXISTS versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instruction_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            content TEXT NOT NULL,
            change_description TEXT DEFAULT '',
            context_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (instruction_id) REFERENCES instructions(id),
            FOREIGN KEY (context_id) REFERENCES contexts(id)
        );

        CREATE TABLE IF NOT EXISTS variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_instruction_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_instruction_id) REFERENCES instructions(id)
        );

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
        );

        CREATE TABLE IF NOT EXISTS iteration_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_instruction_id INTEGER,
            child_instruction_id INTEGER,
            parent_version INTEGER,
            child_version INTEGER,
            change_type TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_instruction_id) REFERENCES instructions(id),
            FOREIGN KEY (child_instruction_id) REFERENCES instructions(id)
        );
    """)

    # Migrations: add columns if they don't exist
    migrations = [
        ("instructions", "ALTER TABLE instructions ADD COLUMN context_id INTEGER"),
        ("versions", "ALTER TABLE versions ADD COLUMN context_id INTEGER"),
        ("feedback", "ALTER TABLE feedback ADD COLUMN version_number INTEGER"),
        ("feedback", "ALTER TABLE feedback ADD COLUMN manual_edits INTEGER DEFAULT 0"),
    ]

    for table, sql in migrations:
        try:
            conn.execute(sql)
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column likely already exists

    conn.commit()
    conn.close()

init_db()

