import os
import json
import bcrypt

CREDENTIALS_FILE = "./.secrets/.users.json"


def load_users() -> dict:
    if not os.path.exists(CREDENTIALS_FILE):
        return {}
    try:
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def secure_opener(path, flags):
    """Guarantees the file is created with 600 permissions (Owner Read/Write Only)"""
    return os.open(path, flags, 0o600)


def save_users(data: dict):
    # overrides the already written data.
    dir_name = os.path.dirname(CREDENTIALS_FILE)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
        os.chmod(dir_name, 0o700)

    with open(CREDENTIALS_FILE, "w", opener=secure_opener) as f:
        json.dump(data, f, indent=4)


def register_user(username: str, plain_password: str):
    users = load_users()
    if username in users:
        print(f"User {username} is already registered!")
        return False
    # Generate unique salt and hash the password (rounds=12 is the production standard)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt(rounds=12))

    users[username] = hashed.decode("utf-8")
    save_users(users)
    return True


def verify_user(username: str, plain_password: str):
    users = load_users()
    if username not in users:
        return False
    stored_hash = users[username].encode("utf-8")
    # check if they match
    return bcrypt.checkpw(plain_password.encode("utf-8"), stored_hash)
