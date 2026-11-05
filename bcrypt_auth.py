import os
import json
import bcrypt
import sqlite3
from config import USERS_DB
import pandas as pd

class User:
    def __init__(self, user_name, enc_password, dept_ids):
        self.id = None
        self.user_name = user_name
        self.enc_password = enc_password
        self.dept_ids = dept_ids
        self.active = 1

def get_userdata_connection():
    """Returns connection to the metadata store."""
    return sqlite3.connect(USERS_DB, check_same_thread=False)

def init_users():
    conn = get_userdata_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS USERS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                enc_password TEXT,
                dept_ids,
                active INTEGER DEFAULT 1
            )
        """)
        print(f"Done with creating user table")
    finally:
        conn.commit()
        conn.close()

def load_users() -> dict:
    """ connect to the sqlite db, fetch all the active users"""
    conn = get_userdata_connection()
    df = pd.read_sql("SELECT * FROM users where active = 1", conn)
    conn.close()
    user_dict = {
        row.user_name: User(
            user_name=row.user_name,
            enc_password=row.enc_password,
            dept_ids=row.dept_ids)
        for row in df.itertuples(index=False)
    }
    return user_dict

def register_user(user_name: str, plain_password: str, dept_ids: str):
    users = load_users()
    if user_name in users:
        print(f"User {user_name} already exist!")
        return False
    # encrypt the password and generate its hash
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt(rounds=12))
    user = User(user_name=user_name, enc_password=hashed.decode('utf-8'), dept_ids=dept_ids)
    save_user(user)
    return True

def save_user(user: User): 
    conn = get_userdata_connection()
    try:
        cursor = conn.cursor()
        sql = "INSERT INTO USERS (user_name, enc_password, dept_ids, active) VALUES (?, ?, ?, 1)"
        cursor.execute(sql, (user.user_name, user.enc_password, user.dept_ids))

    finally:
        conn.commit()
        conn.close()

def verify_user(username: str, plain_password: str):
    users = load_users()
    if username not in users:
        return False
    print(f"user {username} exist in db, dept_ids: {users.get(username).dept_ids}")
    stored_hashed_password = users.get(username).enc_password.encode('utf-8')
    # check if they match
    return (bcrypt.checkpw(plain_password.encode("utf-8"), stored_hashed_password), users.get(username).dept_ids)
