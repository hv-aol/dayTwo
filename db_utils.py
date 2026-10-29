import sqlglot
import streamlit as st
import logging

import os
import crypto_utils

logger = logging.getLogger(__name__)

def load_system_key() -> str:
    """Reads the key from the locked system file."""
    key_path = os.path.expanduser("./.secrets/.master_key")
    if not os.path.exists(key_path):
        raise FileNotFoundError("Critical Error: Secure key file (./.secrets/.master_key) missing!")
    
    # Read the file containing the APP_DECRYPTION_KEY="xyz"
    with open(key_path, "r") as f:
        for line in f:
            if line.startswith("APP_DECRYPTION_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise ValueError("Critical Error: Key not found inside .secrets/.master_key")

def get_db_con_dict():
    crypto_key = load_system_key()
    encrypted_pass = os.getenv("DB_USER_PWD")
    # decrypt it 
    decrypted_pwd = crypto_utils.decrypt_pwd(encrypted_pass, crypto_key)
    return {
        "host": os.getenv("DB_SERVER_IP"),
        "port": os.getenv("DB_SERVER_PORT"),
        "user": os.getenv("DB_USER_NAME"),
        "password": decrypted_pwd,
        "database": os.getenv("DB_NAME")
    }


def validate_query_gen_by_llm(query, target_db):
    logger.debug(f"Target db = {target_db}, SQL to validate: {query}")
    try:
        parsed_query = sqlglot.parse_one(query, dialect=target_db)
        logger.info(f"SQL validation passed!")
    except ParseError as e:
        logger.error(f"SQL Validation failed with error {e}")

