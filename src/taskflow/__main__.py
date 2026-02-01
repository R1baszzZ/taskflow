import argparse
import sqlite3
from taskflow import db



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    parser.add_argument("arg1", nargs="?")  # name, id, or title depending on command

    # Optional flags used by add-task
    parser.add_argument("--desc", dest="desc", default=None)
    parser.add_argument("--assignee", dest="assignee_id", type=int, default=None)

    args = parser.parse_args()
    # command add user
    if args.command == "add-user":
        if not args.arg1:
            print("Error: add-user requires a name")
            return
        else:
            try:
                user_id = db.add_user(args.arg1)
                print(f"User '{args.arg1}' added with id {user_id}.")
            except sqlite3.IntegrityError:
                print(f"User '{args.arg1}' already exists")        
    
    # command list users
    elif args.command == "list-users":
        users = db.list_users()
        if not users:
            print("Your list is empty")
            return
        for user_id, name in users:
            print(f"{user_id} | {name}")  
    
    # command delete user
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

    elif args.command == "add-task":
        title = (args.arg1 or "").strip()
        if not title:
            print("Error: add-task requires a title")
            return

        # Normalize description: None stays None, "" becomes None
        description = args.desc
        if description is not None:
            description = description.strip()
            if description == "":
                description = None

        # Assignee: if provided but not found, store NULL (None)
        assignee_id = args.assignee_id
        if assignee_id is not None:
            if assignee_id < 1:
                print("Error: assignee id must be a positive number")
                return
            user_ids = {uid for uid, _ in db.list_users()}
            if assignee_id not in user_ids:
                print(f"Warning: no user with id {assignee_id}; storing assignee as NULL")
                assignee_id = None

        task_id = db.add_task(title, description, assignee_id)
        print(f"Task '{title}' added with id {task_id}.")

    
    else:
        print(f"Unknown command : '{args.command}'")
        return
    

if __name__ == "__main__":
    main()