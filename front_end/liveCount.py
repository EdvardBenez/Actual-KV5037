#Author: Marcel Majtyka (24005777)
#Python file to calculate how many people are inside the ELC (liveCount).
#Used https://datalemur.com/sql-tutorial/sql-case-statement and https://www.w3schools.com/sql/sql_case.asp

import sqlite3, os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'detections.db')

def calc_live_count():
    
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    #Live Count Logic - Works by summing today's entries and minusing from exits.
    liveCountQuery = cur.execute("""
        SELECT SUM(CASE WHEN direction = 'in' THEN 1 ELSE 0 END) - 
                SUM(CASE WHEN direction = 'out' THEN 1 ELSE 0 END)
        FROM Detections
        WHERE DATE(timeStamp) = DATE('now')
    """)

    LiveCountResult = liveCountQuery.fetchone()
    #returning 1st item as SQLite returns a tuple, and setting default value of 0 if result is invalid or <0
    return LiveCountResult[0] if LiveCountResult[0] >=0 else 0 
