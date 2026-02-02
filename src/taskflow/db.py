import os
import sqlite3
import sys
from pathlib import Path

def _get_data_dir() -> Path:
    # Keep local ./data for dev runs, but use a user-writable folder in frozen apps.
    if not getattr(sys, "frozen", False):
        return Path("data")

    if sys.platform == "win32":
        base_dir = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base_dir) / "TaskFlow"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "TaskFlow"
    return Path.home() / ".local" / "share" / "TaskFlow"


# folder to store the sqlite database
DATA_DIR = _get_data_dir()
# full path to the database file
DB_PATH = DATA_DIR / "taskflow.db"

# open a connection and make sure foreign keys are enabled
def get_connection() -> sqlite3.Connection:
    global DATA_DIR, DB_PATH
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # Fallback to a user-writable folder if the current directory is locked down.
        fallback_dir = _get_data_dir()
        fallback_dir.mkdir(parents=True, exist_ok=True)
        DATA_DIR = fallback_dir
        DB_PATH = DATA_DIR / "taskflow.db"
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    initialize_db(conn)
    return conn


def initialize_db(conn: sqlite3.Connection) -> None:
    # These are safe to run every time (CREATE TABLE IF NOT EXISTS).
    # users table
    create_users_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
    """

    # tasks table
    create_tasks_sql = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'todo' CHECK(status IN('todo', 'doing', 'done')),
            assignee_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        );
    """

    cur = conn.cursor()
    cur.execute(create_users_sql)
    cur.execute(create_tasks_sql)
    conn.commit()

# add a user and return the new id
def add_user(name: str) -> int:
    # Normalize input so we don't store empty names.
    name = name.strip()
    if not name:
        raise ValueError("name cannot be empty")

    # connect and insert
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name) VALUES (?)", (name,))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

# return all users as (id, name)
def list_users() -> list[tuple[int, str]]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM users ORDER BY id")
        return cur.fetchall()
    finally:
        conn.close()

# delete a user by id and return True if something was deleted
def delete_user(user_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

# add a task and return the new id
def add_task(title: str, description: str | None, assignee_id: int | None):
    # Title is required; description can be empty/None.
    title = title.strip()
    if not title:
        raise ValueError("title cannot be empty")
    
    if description is not None:
        # We normalize empty strings to None so SQLite stores NULL.
        description = description.strip()
        if description == "":
            description = None

    # If assignee doesn't exist, store NULL and warn the user.
    if assignee_id is not None:
        if assignee_id < 1:
            raise ValueError("assignee id must be a positive number")
        user_ids = {uid for uid, _ in list_users()}
        if assignee_id not in user_ids:
            print(f"Warning: no user with id {assignee_id}; storing assignee as NULL")
            assignee_id = None

    # connect and insert
    conn = get_connection()
    try:
        cur = conn.cursor()
        sql = """    
        INSERT INTO tasks (title, description, assignee_id)
        VALUES (?, ?, ?)
        """
        cur.execute(sql, (title, description, assignee_id))         

        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()    

# update a task status by id
def update_task_status(task_id: int, status: str) -> bool:
    # Keep status values consistent.
    status = status.strip().lower()
    if status not in {"todo", "doing", "done"}:
        raise ValueError("status must be one of: todo, doing, done")

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, task_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

# update task assignee by id (set to None to unassign)
def update_task_assignee(task_id: int, assignee_id: int | None) -> bool:
    # Allow clearing assignee with None.
    if assignee_id is not None:
        if assignee_id < 1:
            raise ValueError("assignee id must be a positive number")
        user_ids = {uid for uid, _ in list_users()}
        if assignee_id not in user_ids:
            print(f"Warning: no user with id {assignee_id}; storing assignee as NULL")
            assignee_id = None

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE tasks SET assignee_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (assignee_id, task_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

# list tasks as (title, status, assignee_name)
def list_tasks(
    status: str | None = None,
    assignee_id: int | None = None,
    title_query: str | None = None,
) -> list[tuple[int, str, str, str | None, str]]:
    # Filters are optional; we only add WHERE clauses when provided.
    if status is not None:
        status = status.strip().lower()
        if status not in {"todo", "doing", "done"}:
            raise ValueError("status must be one of: todo, doing, done")

    if assignee_id is not None:
        if assignee_id < 1:
            raise ValueError("assignee id must be a positive number")

    if title_query is not None:
        title_query = title_query.strip()
        if title_query == "":
            title_query = None

    conn = get_connection()
    try:
        cur = conn.cursor()
        sql = """
            SELECT tasks.id, tasks.title, tasks.status, users.name, tasks.created_at
            FROM tasks LEFT JOIN users ON tasks.assignee_id = users.id
        """
        where_clauses = []
        params: list[object] = []

        if status is not None:
            where_clauses.append("tasks.status = ?")
            params.append(status)

        if assignee_id is not None:
            where_clauses.append("tasks.assignee_id = ?")
            params.append(assignee_id)

        if title_query is not None:
            where_clauses.append("tasks.title LIKE ?")
            like_value = f"%{title_query}%"
            params.append(like_value)

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        sql += " ORDER BY tasks.created_at, tasks.id"

        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()


def list_tasks_by_statuses(statuses: list[str]) -> list[tuple[int, str, str, str | None, str]]:
    # Single query for multiple statuses (used by the UI active filter).
    if not statuses:
        return []

    normalized = []
    for status in statuses:
        value = status.strip().lower()
        if value not in {"todo", "doing", "done"}:
            raise ValueError("status must be one of: todo, doing, done")
        normalized.append(value)

    placeholders = ", ".join(["?"] * len(normalized))
    sql = f"""
        SELECT tasks.id, tasks.title, tasks.status, users.name, tasks.created_at
        FROM tasks LEFT JOIN users ON tasks.assignee_id = users.id
        WHERE tasks.status IN ({placeholders})
        ORDER BY tasks.created_at, tasks.id
    """

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, normalized)
        return cur.fetchall()
    finally:
        conn.close()

def get_task(task_id: int) -> tuple[int, str, str | None, str, int | None, str, str | None] | None:
    # Returns the raw task row so the UI can prefill the edit dialog.
    conn = get_connection()
    try:
        cur = conn.cursor()
        sql = """
            SELECT id, title, description, status, assignee_id, created_at, updated_at
            FROM tasks
            WHERE id = ?
        """
        cur.execute(sql, (task_id,))
        return cur.fetchone()
    finally:
        conn.close()


def update_task(task_id: int, title: str, description: str | None, assignee_id: int | None) -> bool:
    # Update title/description/assignee in one place so UI doesn't duplicate logic.
    title = title.strip()
    if not title:
        raise ValueError("title cannot be empty")

    if description is not None:
        # Keep NULLs clean for empty descriptions.
        description = description.strip()
        if description == "":
            description = None

    if assignee_id is not None:
        if assignee_id < 1:
            raise ValueError("assignee id must be a positive number")
        user_ids = {uid for uid, _ in list_users()}
        if assignee_id not in user_ids:
            print(f"Warning: no user with id {assignee_id}; storing assignee as NULL")
            assignee_id = None

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, assignee_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (title, description, assignee_id, task_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_task(task_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()
