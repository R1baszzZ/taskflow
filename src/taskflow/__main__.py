import argparse
import sqlite3
from taskflow import db

# entry point for the CLI app
def main():
    # set up the command line parser
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    parser.add_argument("arg1", nargs="?")  # name, id, or title depending on command
    parser.add_argument("arg2", nargs="?")  # second arg for commands like update-task-status

    # optional flags used by add-task and list-tasks
    parser.add_argument("--desc", dest="desc", default=None)
    parser.add_argument("--assignee", dest="assignee_id", default=None)
    parser.add_argument("--assignee-name", dest="assignee_name", default=None)
    parser.add_argument("--status", dest="status", default=None)

    # read what the user typed
    args = parser.parse_args()
    # command: add user
    if args.command == "add-user":
        if not args.arg1:
            print("Error: add-user requires a name")
            return
        else:
            try:
                # try to save the user in the DB
                user_id = db.add_user(args.arg1)
                print(f"User '{args.arg1}' added with id {user_id}.")
            except sqlite3.IntegrityError:
                print(f"User '{args.arg1}' already exists")        
    
    # command: list users
    elif args.command == "list-users":
        users = db.list_users()
        if not users:
            print("Your list is empty")
            return
        for user_id, name in users:
            print(f"{user_id} | {name}")  
    
    # command: delete user
    elif args.command == "delete-user":
        if not args.arg1:
            print("Error: delete-user requires a user id")
            return

        try:
            user_id = int(args.arg1)
        except ValueError:
            print("Error: user id must be a number")
            return

        if user_id < 1:
            print("Error: user id must be a positive number")
            return

        # figure out the user's name (if it exists) before deleting
        user_name = None
        
        for uid, name in db.list_users():
            if uid == user_id:
                user_name = name
                break
        
        # delete from DB and show a friendly message
        deleted = db.delete_user(user_id)
        if deleted:
            if user_name:
                print(f"User '{user_name}' (id {user_id}) was successfully deleted.")
            else:
                print(f"User with id {user_id} was successfully deleted.")
        else:
            print(f"No user found with id {user_id}.")

    elif args.command == "add-task":
        # title comes from arg1
        title = (args.arg1 or "").strip()
        if not title:
            print("Error: add-task requires a title")
            return

        # normalize description: None stays None, "" becomes None
        description = args.desc
        if description is not None:
            description = description.strip()
            if description == "":
                description = None

        # parse assignee id if provided
        assignee_id = None
        if args.assignee_id is not None:
            try:
                assignee_id = int(args.assignee_id)
            except ValueError:
                print("Error: assignee id must be a number")
                return

        # save the task
        task_id = db.add_task(title, description, assignee_id)
        print(f"Task '{title}' added with id {task_id}.")

    # command: list tasks
    elif args.command == "list-tasks":
        assignee_filter = args.assignee_id
        if assignee_filter is not None:
            assignee_text = str(assignee_filter).strip().lower()
            if assignee_text in {"none", "unassigned"}:
                assignee_filter = "__UNASSIGNED__"
            else:
                try:
                    assignee_filter = int(assignee_text)
                except ValueError:
                    print("Error: assignee must be a user id or 'none'")
                    return
        try:
            tasks = db.list_tasks(
                status=args.status,
                assignee_id=assignee_filter,
                assignee_name=args.assignee_name,
            )
        except ValueError as exc:
            print(f"Error: {exc}")
            return
        if not tasks:
            print("Your list is empty")
            return
        for title, status, assignee_name in tasks:
            assignee_display = assignee_name or "—"
            print(f"{title} | {status} | {assignee_display}")

    # command: update task status by id
    elif args.command == "update-task-status":
        if not args.arg1:
            print("Error: update-task-status requires a task id")
            return

        try:
            task_id = int(args.arg1)
        except ValueError:
            print("Error: task id must be a number")
            return

        status = args.arg2
        if not status:
            print("Error: update-task-status requires a status (todo|doing|done)")
            return

        try:
            updated = db.update_task_status(task_id, status)
        except ValueError as exc:
            print(f"Error: {exc}")
            return

        if updated:
            print(f"Task {task_id} updated to '{status}'.")
        else:
            print(f"No task found with id {task_id}.")

    
    else:
        # fallback for unknown commands
        print(f"Unknown command : '{args.command}'")
        return
    

# only run main() when this file is executed directly
if __name__ == "__main__":
    main()