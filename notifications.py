# notifications.py — Real-time Notifications System
import sqlite3
from datetime import datetime

DB_FILE = "pdf_brain.db"

def init_notif_db():
    """Notification Table बनाउने"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        title TEXT,
        message TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()

init_notif_db()

def add_notification(user_id, title, message):
    """नयाँ सूचना थप्ने"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO notifications (user_id, title, message, created_at) VALUES (?, ?, ?, ?)",
                  (user_id, title, message, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[NOTIF ERROR] {e}")
        return False

def get_unread_notifications(user_id):
    """नपढेका सूचनाहरू ल्याउने"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM notifications WHERE user_id=? AND is_read=0 ORDER BY created_at DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_as_read(user_id):
    """सबै सूचना पढिएको चिन्ह लगाउने"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()