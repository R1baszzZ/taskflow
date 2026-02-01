import sqlite3
from pathlib import Path

# folder to store the sqlite database
DATA_DIR = Path("data")
# full path to the database file
DB_PATH = DATA_DIR / "taskflow.db"

# open a connection and make sure foreign keys are enabled
def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# add a user and return the new id
def add_user(name: str) -> int:
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
    title = title.strip()
    if not title:
        raise ValueError("title cannot be empty")
    
    if description is not None:
        description = description.strip()
        if description == "":
            description = None

    # assignee: if provided but not found, store NULL (None)
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

# list tasks as (title, status, assignee_name)
def list_tasks(
    status: str | None = None,
    assignee_id: int | str | None = None,
    assignee_name: str | None = None,
) -> list[tuple[str, str, str | None]]:
    if status is not None:
        status = status.strip().lower()
        if status not in {"todo", "doing", "done"}:
            raise ValueError("status must be one of: todo, doing, done")

    if assignee_id is not None and assignee_id != "__UNASSIGNED__":
        if not isinstance(assignee_id, int):
            raise ValueError("assignee id must be a number")
        if assignee_id < 1:
            raise ValueError("assignee id must be a positive number")

    if assignee_name is not None:
        assignee_name = assignee_name.strip()
        if assignee_name == "":
            assignee_name = None

    conn = get_connection()
    try:
        cur = conn.cursor()
        sql = """
            SELECT tasks.title, tasks.status, users.name
            FROM tasks LEFT JOIN users ON tasks.assignee_id = users.id
        """
        where_clauses = []
        params: list[object] = []

        if status is not None:
            where_clauses.append("tasks.status = ?")
            params.append(status)

        if assignee_id == "__UNASSIGNED__":
            where_clauses.append("tasks.assignee_id IS NULL")
        elif assignee_id is not None:
            where_clauses.append("tasks.assignee_id = ?")
            params.append(assignee_id)

        if assignee_name is not None:
            where_clauses.append("users.name = ?")
            params.append(assignee_name)

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        sql += " ORDER BY tasks.created_at, tasks.id"

        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()
