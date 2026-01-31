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






if __name__ == "__main__":
    main()