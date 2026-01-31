import sqlite3
from pathlib import Path


DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "taskflow.db"

def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def add_user(name: str) -> int:
    name = name.strip()
    if not name:
        raise ValueError("name cannot be empty")

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name) VALUES (?)", (name,))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()