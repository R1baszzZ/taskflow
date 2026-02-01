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

def list_users() -> list[tuple[int, str]]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM users ORDER BY id")
        return cur.fetchall()
    finally:
        conn.close()

def delete_user(user_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def add_task(title: str, description: str | None, assignee_id: int | None):
    title = title.strip()
    if not title:
        raise ValueError("title cannot be empty")
    
    if description is not None:
        description = description.strip()
        if description == "":
            description = None

    conn = get_connection()
    try:
        cur = conn.cursor()
        sql = """    
        INSERT INTO tasks (title, description, assignee_id)
        VALUES (?, ?, (SELECT id FROM users WHERE id = ?))
        """
        cur.execute(sql, (title, description, assignee_id))         

        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()    