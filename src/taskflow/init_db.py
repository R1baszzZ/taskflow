import sqlite3
from pathlib import Path

# creates the sqlite database and tables
def main():
    # in here im using the path library to create a directory called data
    DATA_DIR = Path("data")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # im assigning the directory with the taskflow.db file to DB_PATH
    DB_PATH = DATA_DIR / "taskflow.db"

    # activating foreign keys and connecting path to sqlite
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    # users table
    CREATE_USERS_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
    """
    # commiting the connection
    cur = conn.cursor()
    cur.execute(CREATE_USERS_TABLE_SQL)

    # tasks table
    CREATE_TASKS_TABLE_SQL = """
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
    # commiting the connection
    cur.execute(CREATE_TASKS_TABLE_SQL)
    conn.commit()

    conn.close()

    # quick success message
    print(f"DB initialized at: {DB_PATH}")

# only run when executed directly
if __name__ == "__main__":
    main()
    