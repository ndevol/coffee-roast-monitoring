import sqlite3

conn = None

try:
    conn = sqlite3.connect("data/roast_data.db")

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM roasts")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
except Exception as e:
    print(f"Error: {e}")
finally:
    if conn:
        conn.close()
