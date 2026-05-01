import sqlite3
import datetime
import os

conn = sqlite3.connect("detections.db")
cursor = conn.cursor()

def db_setup():
# Database setup to create Detections table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Detections ( 
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            timeStamp  TEXT NOT NULL,
            direction  TEXT NOT NULL
        )
    """)

    conn.commit()
    return conn, cursor

