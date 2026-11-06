# security.py — PDF Brain Security System
import os
import sqlite3
from datetime import datetime, timedelta

DB_FILE = "pdf_brain.db"

def _get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_security_db():
    conn = _get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        action TEXT,
        target TEXT,
        status TEXT,
        details TEXT,
        timestamp TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS security_settings (
        username TEXT PRIMARY KEY,
        require_approval INTEGER DEFAULT 1,
        failed_login_count INTEGER DEFAULT 0,
        locked_until TEXT
    )''')
    conn.commit()
    conn.close()

init_security_db()

def log_action(username, action, target="", status="success", details=""):
    """हरेक कामको रेकर्ड"""
    try:
        conn = _get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO audit_log (username, action, target, status, details, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (username, action, target, status, details, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[AUDIT ERROR] {e}")
        return False

def get_audit_logs(username=None, limit=50):
    conn = _get_conn()
    c = conn.cursor()
    if username:
        c.execute("SELECT * FROM audit_log WHERE username=? ORDER BY timestamp DESC LIMIT ?", (username, limit))
    else:
        c.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]