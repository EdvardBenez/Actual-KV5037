#Author: Marcel Majtyka (24005777)
#Python file to calculate today's peak hour for the ELC.

import sqlite3, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'detections.db')


def calc_peak_hour():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    #Peak Hour Logic - Works by extracting each hour from today, counting records, 
    #grouping and ordering them in descending order, and selecting the top hour.
    todayCountQuery = cur.execute("""
        SELECT strftime('%H', timeStamp) AS hour, count(*) AS count
        FROM Detections
        WHERE direction = 'in' AND DATE(timeStamp) = DATE('now')
        GROUP BY hour
        ORDER BY count DESC
        LIMIT 1             
        """)

    todayCountResult = todayCountQuery.fetchone()
    #Checking if there's no data for today.
    if todayCountResult is None:
        return 'No Data Yet'
    
    #Putting the hour into readable format for dashboard.
    hour = int(todayCountResult[0])
    peakHour = f"{hour}:00 - {hour+1}:00"
    return peakHour
