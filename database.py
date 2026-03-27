
import sqlite3

conn = sqlite3.connect("plates.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS plates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate TEXT,
    confidence INTEGER,
    timestamp TEXT
)
""")

conn.commit()

def save_plate(plate, confidence, timestamp):
    cursor.execute(
        "INSERT INTO plates (plate, confidence, timestamp) VALUES (?, ?, ?)",
        (plate, confidence, timestamp)
    )
    conn.commit()