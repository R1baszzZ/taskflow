import argparse
import sqlite3
from taskflow import db



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    parser.add_argument("name", nargs="?")

    args = parser.parse_args()
    

    if args.command == "add-user":
        if not args.name:
            print("Error: add-user requires a name")
            return
        else:

            try:
                user_id = db.add_user(args.name)
                print(f"User '{args.name}' added with id {user_id}.")
            except sqlite3.IntegrityError:
                print(f"User '{args.name}' already exists")        
    elif args.command == "list-users":
        users = db.list_users()
        if not users:
            print("Your list is empty")
            return
        for user_id, name in users:
            print(f"{user_id} | {name}")  
    else:
        print(f"Unknown command : '{args.command}'")

    






if __name__ == "__main__":
    main()