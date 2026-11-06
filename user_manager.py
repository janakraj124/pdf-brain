# user_manager.py — Per-User Document Management
import os
import shutil
import json
from datetime import datetime


def get_user_docs_path(username):
    """User को PDF folder"""
    path = f"user_docs/{username}"
    os.makedirs(path, exist_ok=True)
    return path


def get_user_db_path(username):
    """User को Vector DB path"""
    path = f"user_databases/{username}/chroma_db"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def save_user_pdf(username, file_bytes, filename):
    """User को document save (PDF, DOCX, Image, TXT)"""
    # Safe filename
    safe_name = "".join(
        c for c in filename
        if c.isalnum() or c in "._- "
    )
    
    # Supported extensions
    supported = [
        ".pdf", ".docx", ".doc", ".txt", ".md",
        ".jpg", ".jpeg", ".png", ".webp", ".bmp"
    ]
    
    if not any(safe_name.lower().endswith(ext) for ext in supported):
        safe_name += ".pdf"  # Default
    
    folder = get_user_docs_path(username)
    filepath = os.path.join(folder, safe_name)
    
    with open(filepath, "wb") as f:
        f.write(file_bytes)
    
    return filepath


def list_user_pdfs(username):
    """User को सबै documents"""
    folder = get_user_docs_path(username)
    
    supported = [
        ".pdf", ".docx", ".doc", ".txt", ".md",
        ".jpg", ".jpeg", ".png", ".webp", ".bmp"
    ]
    
    docs = []
    if not os.path.exists(folder):
        return docs
    
    for f in os.listdir(folder):
        if any(f.lower().endswith(ext) for ext in supported):
            filepath = os.path.join(folder, f)
            ext = f.lower().split(".")[-1]
            
            # Format icon
            icon = {
                "pdf": "📄",
                "docx": "📘", "doc": "📘",
                "jpg": "🖼️", "jpeg": "🖼️", "png": "🖼️",
                "txt": "📝", "md": "📝"
            }.get(ext, "📎")
            
            docs.append({
                "name": f,
                "icon": icon,
                "format": ext.upper(),
                "size": os.path.getsize(filepath),
                "path": filepath,
                "uploaded": datetime.fromtimestamp(
                    os.path.getmtime(filepath)
                ).isoformat()
            })
    
    return sorted(docs, key=lambda x: x["uploaded"], reverse=True)


def list_user_pdfs(username):
    """User को सबै documents (multi-format)"""
    folder = get_user_docs_path(username)
    
    # Supported formats
    supported = [
        ".pdf", ".docx", ".doc", ".txt", ".md",
        ".jpg", ".jpeg", ".png", ".webp", ".bmp"
    ]
    
    docs = []
    
    if not os.path.exists(folder):
        return docs
    
    for f in os.listdir(folder):
        if any(f.lower().endswith(ext) for ext in supported):
            filepath = os.path.join(folder, f)
            ext = f.lower().split(".")[-1]
            
            # Format icon
            icon = {
                "pdf": "📄",
                "docx": "📘",
                "doc": "📘",
                "jpg": "🖼️",
                "jpeg": "🖼️",
                "png": "🖼️",
                "webp": "🖼️",
                "bmp": "🖼️",
                "txt": "📝",
                "md": "📝"
            }.get(ext, "📎")
            
            docs.append({
                "name": f,
                "icon": icon,
                "format": ext.upper(),
                "size": os.path.getsize(filepath),
                "path": filepath,
                "uploaded": datetime.fromtimestamp(
                    os.path.getmtime(filepath)
                ).isoformat()
            })
    
    return sorted(docs, key=lambda x: x["uploaded"], reverse=True)


def delete_user_pdf(username, filename):
    """User को PDF delete"""
    folder = get_user_docs_path(username)
    filepath = os.path.join(folder, filename)
    
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False


def get_user_stats(username):
    """User को stats"""
    pdfs = list_user_pdfs(username)
    
    # Database stats
    db_path = get_user_db_path(username)
    chunks = 0
    
    if os.path.exists(db_path):
        try:
            import chromadb
            client = chromadb.PersistentClient(path=db_path)
            collection = client.get_or_create_collection("user_docs")
            chunks = collection.count()
        except Exception:
            pass
    
    return {
        "username": username,
        "pdf_count": len(pdfs),
        "total_size": sum(p["size"] for p in pdfs),
        "chunks": chunks,
        "pdfs": pdfs
    }


def delete_user_database(username):
    """User को database delete (rebuild को लागि)"""
    db_path = f"user_databases/{username}"
    if os.path.exists(db_path):
        try:
            shutil.rmtree(db_path)
            return True
        except Exception:
            return False
    return True


def get_all_users():
    """सबै users जो PDF upload गरेका छन्"""
    base = "user_docs"
    if not os.path.exists(base):
        return []
    
    users = []
    for u in os.listdir(base):
        if os.path.isdir(os.path.join(base, u)):
            users.append(u)
    
    return sorted(users)