import argparse
import sqlite3
from taskflow import db



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    parser.add_argument("value", nargs="?")

    args = parser.parse_args()
    # command add user
    if args.command == "add-user":
        if not args.value:
            print("Error: add-user requires a name")
            return
        else:
            try:
                user_id = db.add_user(args.value)
                print(f"User '{args.value}' added with id {user_id}.")
            except sqlite3.IntegrityError:
                print(f"User '{args.value}' already exists")        
    
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
        
        user_id = int(args.value)
        if not user_id:
            print("Error: delete-user requires a user id")
            return
        try:
            if user_id < 1:
                print("Error: user id must be a positive number")
                return
        except ValueError:
            
            print("Error: user id must be a number")
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
            
    
    else:
        print(f"Unknown command : '{args.command}'")
        return

    






if __name__ == "__main__":
    main()