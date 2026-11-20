# client_manager.py — Powerful CRM & Project Tracker
import os
import sqlite3
from datetime import datetime

DB_FILE = "pdf_brain.db"

def init_crm_db():
    """CRM को लागि डाटाबेस बनाउने"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # १. Clients Table
    c.execute('''CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        name TEXT,
        email TEXT,
        phone TEXT,
        company TEXT,
        created_at TEXT
    )''')
    
    # २. Projects Table
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        client_id INTEGER,
        title TEXT,
        description TEXT,
        status TEXT,  -- Pending, In Progress, Completed
        budget REAL,
        deadline TEXT,
        created_at TEXT
    )''')
    
    conn.commit()
    conn.close()

init_crm_db()

# --- Clients ---
def add_client(user_id, name, email, phone, company):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO clients (user_id, name, email, phone, company, created_at) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, name, email, phone, company, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return {"success": True}

def get_clients(user_id):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM clients WHERE user_id=?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- Projects ---
def add_project(user_id, client_id, title, description, status, budget, deadline):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO projects (user_id, client_id, title, description, status, budget, deadline, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (user_id, client_id, title, description, status, budget, deadline, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return {"success": True}

def get_projects(user_id):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    # Client को नाम सहित प्रोजेक्ट ल्याउने
    c.execute('''SELECT p.*, c.name as client_name 
                 FROM projects p 
                 LEFT JOIN clients c ON p.client_id = c.id 
                 WHERE p.user_id = ? ORDER BY p.created_at DESC''', (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_project_status(project_id, new_status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE projects SET status=? WHERE id=?", (new_status, project_id))
    conn.commit()
    conn.close()
    return {"success": True}