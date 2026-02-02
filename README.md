# TaskFlow 🧩  
*A simple task manager built while learning Python, databases, and UI design*

## Why I Built This
TaskFlow started as a command-line project to help me practice **Python fundamentals**, **SQLite**, and **project structure**.  
As the project grew, I transitioned it into a **GUI application** to learn how real users interact with software — not just how code runs.

This project reflects how I approach learning:
- build something small
- improve it step by step
- refactor when things get messy
- focus on clarity over cleverness

---

## What TaskFlow Does
TaskFlow lets users manage tasks and users locally using a simple interface.

You can:
- Create users
- Create tasks
- Assign tasks to users (or leave them unassigned)
- View all tasks with their status and assignee
- Update task status
- Store everything locally using SQLite

The goal is not to be feature-complete, but **solid, readable, and extendable**.

---

## Tech Stack
- **Python 3**
- **SQLite** (local database)
- **Tkinter + ttk** (GUI)
- **PyInstaller** (packaged as an executable)
  
---

## Design Decisions (On Purpose)
- **Readable > Clever**  
  I chose clarity over shortcuts so that another student (or recruiter) can follow the code.

- **SQLite instead of an API**  
  This keeps the project self-contained while still teaching real database concepts.

- **No task IDs shown in the UI**  
  Users see *what matters* (task name, status, assignee), not internal identifiers.

  - **UI only runs on Windows**
  
- **Unassigned tasks allowed**  
  Tasks can exist without an assignee to reflect real workflows.

---

## What I Learned
- How SQLite connections and cursors actually work
- How to separate UI logic from database logic
- How small design choices affect UX
- How to refactor without breaking functionality
- How packaging Python apps differs from running scripts

---

## What I Want to Improve Next
- Sorting and filtering tasks
- User roles (admin vs worker)
- Task deadlines and priorities
- Better visual feedback in the UI
- Unit tests for database functions

---

## How to Run
### Option 1: Executable
Download and run the `.exe` (no Python required).

### Option 2: From Source
```bash
pip install -e .

python -m taskflow
