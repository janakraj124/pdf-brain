# audit_logger.py — PDF Brain Central Audit System
import os
import json
import sqlite3
from datetime import datetime

AUDIT_DB = "audit_log.db"


def _get_conn():
    """SQLite connection फर्काउने (auto-init)"""
    conn = sqlite3.connect(AUDIT_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            email TEXT,
            username TEXT,
            purpose TEXT,
            action TEXT,
            status TEXT,
            ip_address TEXT,
            user_agent TEXT,
            details TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_email ON audit_log(email)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_event ON audit_log(event_type)
    """)
    conn.commit()
    return conn


def log_event(event_type, email="", username="", purpose="", action="",
              status="", ip="", ua="", details=None):
    """
    Central audit log.
    
    event_type: 'otp_request', 'otp_verify', 'login', 'signup',
                'password_reset', 'email_sent', 'email_received',
                'spam_blocked', 'rate_limited'
    status: 'success', 'fail', 'blocked', 'error'
    """
    try:
        conn = _get_conn()
        conn.execute(
            """INSERT INTO audit_log
               (timestamp, event_type, email, username, purpose, action,
                status, ip_address, user_agent, details)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                datetime.now().isoformat(),
                event_type,
                (email or "").lower().strip(),
                username or "",
                purpose or "",
                action or "",
                status or "",
                ip or "",
                ua or "",
                json.dumps(details, ensure_ascii=False) if details else ""
            )
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[AUDIT ERROR] {e}")
        return False


def get_audit_logs(email=None, event_type=None, limit=100):
    """Audit logs पढ्ने — filtering सहित"""
    try:
        conn = _get_conn()
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []
        if email:
            query += " AND email = ?"
            params.append(email.lower().strip())
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        columns = [d[0] for d in cursor.description]
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"[AUDIT READ ERROR] {e}")
        return []


def get_audit_stats(email=None, hours=24):
    """पछिल्लो N घण्टाको summary"""
    try:
        conn = _get_conn()
        from datetime import timedelta
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        query = "SELECT event_type, status, COUNT(*) FROM audit_log WHERE timestamp >= ?"
        params = [since]
        if email:
            query += " AND email = ?"
            params.append(email.lower().strip())
        query += " GROUP BY event_type, status"
        cursor = conn.execute(query, params)
        stats = {}
        for event_type, status, count in cursor.fetchall():
            stats.setdefault(event_type, {})[status] = count
        conn.close()
        return stats
    except Exception as e:
        print(f"[AUDIT STATS ERROR] {e}")
        return {}


def cleanup_old_logs(days=90):
    """पुरानो logs मेट्ने (default ९० दिन)"""
    try:
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        conn = _get_conn()
        conn.execute("DELETE FROM audit_log WHERE timestamp < ?", (cutoff,))
        conn.commit()
        deleted = conn.total_changes
        conn.close()
        return deleted
    except Exception as e:
        print(f"[AUDIT CLEANUP ERROR] {e}")
        return 0