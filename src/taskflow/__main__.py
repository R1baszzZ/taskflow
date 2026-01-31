import argparse
import db



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    parser.add_argument("name", nargs="?")

    args = parser.parse_args()
    
    if args.command == "add-user":
        user_id = db.add_user(args.name)
        print(f"User '{args.name}' added with id {user_id}.")
    
    if not args.name:
        print("Error: add-user requires a name")
        return




if __name__ == "__main__":
    main()