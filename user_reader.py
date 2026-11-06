# user_reader.py — Universal Edition
import os
from universal_reader import read_any_document
from user_manager import get_user_docs_path


def read_user_pdfs(username):
    """User को सबै documents पढ्ने (PDF, DOCX, Image, TXT)"""
    folder = get_user_docs_path(username)
    
    if not os.path.exists(folder):
        return {}
    
    # Supported formats
    supported = [
        ".pdf", ".docx", ".doc", ".txt", ".md",
        ".jpg", ".jpeg", ".png", ".webp", ".bmp"
    ]
    
    files = [
        f for f in os.listdir(folder)
        if any(f.lower().endswith(ext) for ext in supported)
    ]
    
    if not files:
        return {}
    
    print(f"📚 {len(files)} documents भेटियो\n")
    
    all_texts = {}
    for filename in files:
        path = os.path.join(folder, filename)
        print(f"📖 पढ्दै: {filename}")
        try:
            text, doc_type = read_any_document(path)
            if text.strip():
                all_texts[filename] = text
                print(f"   ✅ {len(text)} अक्षर ({doc_type})\n")
            else:
                print(f"   ⚠️  खाली\n")
        except Exception as e:
            print(f"   ❌ {e}\n")
    
    return all_texts