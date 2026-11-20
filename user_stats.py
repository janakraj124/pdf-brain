# user_stats.py
import os
import json
import sqlite3

DB_FILE = "pdf_brain.db"

def get_user_dashboard_stats(username):
    """युजरको कुल तथ्याङ्क निकाल्ने"""
    stats = {
        "pdfs": 0,
        "chats": 0,
        "tables": 0,
        "images": 0,
        "agent_runs": 0
    }
    
    # १. PDF गन्ने
    user_docs_path = f"user_docs/{username}"
    if os.path.exists(user_docs_path):
        stats["pdfs"] = len([f for f in os.listdir(user_docs_path) if os.path.isfile(os.path.join(user_docs_path, f))])
        
    # २. History (Chat, Table, Image) गन्ने
    hist_file = f"history_data/{username}.json"
    if os.path.exists(hist_file):
        try:
            with open(hist_file, "r", encoding="utf-8") as f:
                history = json.load(f)
                stats["chats"] = len(history.get("chat", {}))
                stats["tables"] = len(history.get("table", {}))
                stats["images"] = len(history.get("image", {}))
        except:
            pass

    # ३. Agent runs (Audit log बाट)
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM audit_log WHERE username=? AND action='AGENT_TOOL'", (username,))
        row = c.fetchone()
        if row:
            stats["agent_runs"] = row[0]
        conn.close()
    except:
        pass

    return stats