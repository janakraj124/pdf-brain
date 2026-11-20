# file_delivery.py
import os
import uuid
import json
from datetime import datetime, timedelta

DELIVERY_FILE = "delivery_links.json"

def _load_links():
    if not os.path.exists(DELIVERY_FILE):
        return {}
    try:
        with open(DELIVERY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def _save_links(links):
    with open(DELIVERY_FILE, "w", encoding="utf-8") as f:
        json.dump(links, f, indent=2)

def create_delivery_link(username, project_name, file_path, expiry_days=7):
    """ग्राहकलाई फाइल पठाउन लिंक बनाउने"""
    if not os.path.exists(file_path):
        return {"success": False, "error": "फाइल भेटिएन"}

    token = str(uuid.uuid4())[:8]
    links = _load_links()
    
    links[token] = {
        "username": username,
        "project_name": project_name,
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=expiry_days)).isoformat()
    }
    _save_links(links)
    return {"success": True, "token": token}

def get_delivery_file(token):
    """लिंकको टोकनबाट फाइल खोज्ने"""
    links = _load_links()
    if token not in links:
        return None
    
    data = links[token]
    # एक्सपायर भयो कि जाँच्ने
    if datetime.now() > datetime.fromisoformat(data["expires_at"]):
        return None
        
    return data