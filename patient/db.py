import sqlite3
import os

DB_PATH = "data/patient.db"

def get_db_connection():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_logs (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                date                TEXT NOT NULL,
                foods               TEXT,
                activities          TEXT,
                skin_score          INTEGER,
                notes               TEXT,
                created_at          TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()