#Author: Marcel Majtyka (24005777)
#Python file to create a the detections database

import sqlite3, os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'detections.db')

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

def createDB():
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Detections(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timeStamp TEXT,
        direction TEXT
    );""")

    con.commit()
    print("Database created successfully.")
    con.close()




