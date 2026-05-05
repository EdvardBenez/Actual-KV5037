#Author: Marcel Majtyka (24005777)
#Python file to calculate how many people entered the ELC today.
#Used https://www.w3schools.com/sql/sql_count.asp 
import sqlite3, os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'detections.db')

def calc_today_count():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    #Today Count Logic - Works by couting today's entries in the database.
    todayCountQuery = cur.execute("""
        SELECT COUNT(*) 
        FROM Detections
        WHERE direction = 'in' AND DATE(timeStamp) = DATE('now')
    """)

    todayCountResult = todayCountQuery.fetchone()
    return todayCountResult[0] or 0 #Returning 1st item as SQLite returns a tuple, and setting default value of 0 if result is invalid.
