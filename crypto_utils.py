from cryptography.fernet import Fernet

# one time generation
def generate_new_key():
	secret_key = Fernet.generate_key()
	return secret_key.decode('utf-8')

# Use it to encrypt the database password.
def encrypt_pwd(password_raw: str, key_str: str):
	f = Fernet(key_str.encode('utf-8'))
	encrypted_bytes = f.encrypt(password_raw.encode('utf-8'))
	return encrypted_bytes.decode('utf-8')

def decrypt_pwd(password_enc: str, key_str: str):
	f = Fernet(key_str.encode('utf-8'))
	decrypted_bytes = f.decrypt(password_enc.encode('utf-8'))
	return decrypted_bytes.decode('utf-8')

# =====================================================================
# ONE-TIME SETUP SIMULATION (Run this section on your Mac to get your keys)
# =====================================================================
if __name__ == "__main__":
    print("--- ONE-TIME KEY GENERATION ---")
    
    # 1. Generate the master key
    my_key = generate_new_key()
    print(f"1. Put this key inside your locked ~/.prod.env file:\n👉 {my_key}\n")
    
    # 2. Encrypt your database password
    raw_db_password = "stYnWfBTNKW"  # Replace with your real DB pass
    scrambled_pass = encrypt_pwd(raw_db_password, my_key)
    print(f"2. Put this string inside your project's .env file (DB_PASSWORD=...):\n👉 {scrambled_pass}\n")
    
    # 3. Test verification (App sanity check)
    decrypted_test = decrypt_pwd(scrambled_pass, my_key)
    print(f"Verification Check -> Decrypted password matches original: {raw_db_password == decrypted_test}")
