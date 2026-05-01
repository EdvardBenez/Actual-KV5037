import sqlite3 # Author of this script below is: Brandon Ayre w24025960
from flask_bcrypt import Bcrypt
from login import app
from datetime import datetime
import getpass  # hides password input
import os

bcrypt = Bcrypt(app)

#Database file path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'users.db')

# Ask user for details
username = input("Enter admin username: ")
password_input = getpass.getpass("Enter admin password: ")
confirm_password = getpass.getpass("Confirm password: ")

# Check passwords match
if password_input != confirm_password:
    print("Passwords do not match.")
    exit()

# Hash password
hashed_password = bcrypt.generate_password_hash(password_input).decode("utf-8")

# Current timestamp for password tracking
password_changed_at = datetime.now().isoformat()

# Connect to DB
con = sqlite3.connect(DB_PATH)
cur = con.cursor()

# Ensure table exists (with password_changed_at column)
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    password_changed_at TEXT
)
""")

# Insert user
try:
    cur.execute(
        "INSERT INTO users (username, password, password_changed_at) VALUES (?, ?, ?)",
        (username, hashed_password, password_changed_at)
    )
    con.commit()
    print("Admin account created successfully.")
except sqlite3.IntegrityError:
    print("Username already exists.")

con.close()
