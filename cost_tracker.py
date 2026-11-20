# cost_tracker.py
import sqlite3
from datetime import datetime

DB_FILE = "pdf_brain.db"

def init_cost_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cost_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        service TEXT,
        amount REAL,
        timestamp TEXT
    )''')
    conn.commit()
    conn.close()

init_cost_db()

def track_cost(username, service="Gemini", amount=0.0001):
    """एक पटक API प्रयोग गर्दा खर्च रेकर्ड गर्ने"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO cost_tracking (username, service, amount, timestamp) VALUES (?, ?, ?, ?)",
              (username, service, amount, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_user_cost(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT SUM(amount) FROM cost_tracking WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row and row[0] else 0.0