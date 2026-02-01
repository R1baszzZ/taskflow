import argparse
import sqlite3
import sys
from taskflow import db


def _pause():
    input("Press Enter to continue...")


def _prompt(text: str, allow_empty: bool = False) -> str | None:
    value = input(text).strip()
    if value == "" and not allow_empty:
        return None
    return value


def _prompt_int(text: str, allow_empty: bool = False) -> int | None:
    value = _prompt(text, allow_empty=allow_empty)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _assignee_filter(value: str) -> int | str:
    text = value.strip().lower()
    if text in {"none", "unassigned"}:
        return "__UNASSIGNED__"
    try:
        return int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("assignee must be a user id or 'none'") from exc


def _print_tasks(tasks: list[tuple[str, str, str | None]]):
    if not tasks:
        print("Your list is empty")
        return
    for title, status, assignee_name in tasks:
        assignee_display = assignee_name or "—"
        print(f"{title} | {status} | {assignee_display}")


def _handle_add_user(args: argparse.Namespace):
    name = (args.name or "").strip()
    if not name:
        print("Error: name is required")
        return
    try:
        user_id = db.add_user(name)
        print(f"User '{name}' added with id {user_id}.")
    except sqlite3.IntegrityError:
        print(f"User '{name}' already exists")


def _handle_list_users(_: argparse.Namespace):
    users = db.list_users()
    if not users:
        print("Your list is empty")
        return
    for user_id, name in users:
        print(f"{user_id} | {name}")


def _handle_delete_user(args: argparse.Namespace):
    user_id = args.user_id
    if user_id < 1:
        print("Error: user id must be a positive number")
        return
    user_name = None
    for uid, name in db.list_users():
        if uid == user_id:
            user_name = name
            break
    deleted = db.delete_user(user_id)
    if deleted:
        if user_name:
            print(f"User '{user_name}' (id {user_id}) was successfully deleted.")
        else:
            print(f"User with id {user_id} was successfully deleted.")
    else:
        print(f"No user found with id {user_id}.")


def _handle_add_task(args: argparse.Namespace):
    title = (args.title or "").strip()
    if not title:
        print("Error: title is required")
        return
    description = args.desc
    if description is not None:
        description = description.strip()
        if description == "":
            description = None
    try:
        task_id = db.add_task(title, description, args.assignee)
    except ValueError as exc:
        print(f"Error: {exc}")
        return
    print(f"Task '{title}' added with id {task_id}.")


def _handle_list_tasks(args: argparse.Namespace):
    try:
        tasks = db.list_tasks(
            status=args.status,
            assignee_id=args.assignee,
            assignee_name=args.assignee_name,
        )
    except ValueError as exc:
        print(f"Error: {exc}")
        return
    _print_tasks(tasks)


def _handle_update_task_status(args: argparse.Namespace):
    try:
        updated = db.update_task_status(args.task_id, args.status)
    except ValueError as exc:
        print(f"Error: {exc}")
        return
    if updated:
        print(f"Task {args.task_id} updated to '{args.status}'.")
    else:
        print(f"No task found with id {args.task_id}.")


def _ui_add_user():
    name = _prompt("Name: ")
    if not name:
        print("Name is required.")
        return
    try:
        user_id = db.add_user(name)
        print(f"User '{name}' added with id {user_id}.")
    except sqlite3.IntegrityError:
        print(f"User '{name}' already exists")


def _ui_list_users():
    _handle_list_users(argparse.Namespace())


def _ui_delete_user():
    users = db.list_users()
    if not users:
        print("Your list is empty")
        return
    for user_id, name in users:
        print(f"{user_id} | {name}")
    user_id = _prompt_int("User id to delete: ")
    if user_id is None:
        print("User id must be a number.")
        return
    _handle_delete_user(argparse.Namespace(user_id=user_id))


def _ui_add_task():
    title = _prompt("Title: ")
    if not title:
        print("Title is required.")
        return
    description = _prompt("Description (optional): ", allow_empty=True)
    if description == "":
        description = None
    assignee_id = _prompt_int("Assignee id (optional): ", allow_empty=True)
    try:
        task_id = db.add_task(title, description, assignee_id)
        print(f"Task '{title}' added with id {task_id}.")
    except ValueError as exc:
        print(f"Error: {exc}")


def _ui_list_tasks():
    tasks = db.list_tasks()
    _print_tasks(tasks)


def _ui_update_task_status():
    tasks = db.list_tasks_with_ids()
    if not tasks:
        print("Your list is empty")
        return
    for idx, (task_id, title, status, assignee_name) in enumerate(tasks, start=1):
        assignee_display = assignee_name or "—"
        print(f"{idx}) {title} | {status} | {assignee_display}")
    choice = _prompt_int("Select task number: ")
    if choice is None or choice < 1 or choice > len(tasks):
        print("Invalid selection.")
        return
    task_id = tasks[choice - 1][0]
    status_input = _prompt("New status (todo/doing/done): ")
    if not status_input:
        print("Status is required.")
        return
    try:
        updated = db.update_task_status(task_id, status_input)
    except ValueError as exc:
        print(f"Error: {exc}")
        return
    if updated:
        print("Task updated.")
    else:
        print("Task not found.")


def run_ui():
    while True:
        print("\nTaskFlow")
        print("1) Add user")
        print("2) List users")
        print("3) Delete user")
        print("4) Add task")
        print("5) List tasks")
        print("6) Update task status")
        print("0) Exit")

        choice = _prompt("Choose an option: ")
        if choice == "1":
            _ui_add_user()
            _pause()
        elif choice == "2":
            _ui_list_users()
            _pause()
        elif choice == "3":
            _ui_delete_user()
            _pause()
        elif choice == "4":
            _ui_add_task()
            _pause()
        elif choice == "5":
            _ui_list_tasks()
            _pause()
        elif choice == "6":
            _ui_update_task_status()
            _pause()
        elif choice == "0":
            print("Goodbye!")
            return
        else:
            print("Invalid choice.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="taskflow")
    subparsers = parser.add_subparsers(dest="command")

    add_user = subparsers.add_parser("add-user", help="Add a new user")
    add_user.add_argument("name")
    add_user.set_defaults(func=_handle_add_user)

    list_users = subparsers.add_parser("list-users", help="List all users")
    list_users.set_defaults(func=_handle_list_users)

    delete_user = subparsers.add_parser("delete-user", help="Delete a user by id")
    delete_user.add_argument("user_id", type=int)
    delete_user.set_defaults(func=_handle_delete_user)

    add_task = subparsers.add_parser("add-task", help="Add a new task")
    add_task.add_argument("title")
    add_task.add_argument("--desc", dest="desc", default=None)
    add_task.add_argument("--assignee", dest="assignee", type=int, default=None)
    add_task.set_defaults(func=_handle_add_task)

    list_tasks = subparsers.add_parser("list-tasks", help="List tasks")
    list_tasks.add_argument("--status", choices=["todo", "doing", "done"], default=None)
    list_tasks.add_argument("--assignee", type=_assignee_filter, default=None)
    list_tasks.add_argument("--assignee-name", dest="assignee_name", default=None)
    list_tasks.set_defaults(func=_handle_list_tasks)

    update_status = subparsers.add_parser("update-task-status", help="Update task status by id")
    update_status.add_argument("task_id", type=int)
    update_status.add_argument("status", choices=["todo", "doing", "done"])
    update_status.set_defaults(func=_handle_update_task_status)

    ui = subparsers.add_parser("ui", help="Open interactive menu")
    ui.set_defaults(func=lambda _: run_ui())

    return parser


# entry point for the CLI app
def main(argv: list[str] | None = None):
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        run_ui()
        return

    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return

    try:
        args.func(args)
    except sqlite3.Error as exc:
        print(f"Error: {exc}")


# only run main() when this file is executed directly
if __name__ == "__main__":
    main()