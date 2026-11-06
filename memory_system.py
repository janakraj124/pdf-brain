# memory_system.py — Long-term Memory for PDF Brain
import os
import re
import json
import sqlite3
from datetime import datetime
from google import genai
from dotenv import load_dotenv

load_dotenv()

DB_FILE = "pdf_brain.db"
MODEL = "gemini-3.5-flash-lite"


def _get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_memory_db():
    """Memory tables बनाउने"""
    conn = _get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    memory_type TEXT,        -- 'fact', 'preference', 'summary', 'profile'
                    content TEXT,
                    importance INTEGER DEFAULT 5,  -- 1-10
                    created_at TEXT,
                    last_used TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS conversation_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    summary TEXT,
                    msg_count INTEGER,
                    created_at TEXT
                )''')
    conn.commit()
    conn.close()


init_memory_db()

def _extract_key_values(text: str) -> set:
    """Email, phone, URL जस्ता unique data निकाल्ने"""
    keys = set()
    # Email
    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    keys.update([e.lower() for e in emails])
    # Phone (10+ digits)
    phones = re.findall(r'\+?\d{10,}', text)
    keys.update([p.replace("+", "") for p in phones])
    # URLs
    urls = re.findall(r'https?://[^\s]+', text)
    keys.update([u.lower() for u in urls])
    return keys

# ============================================================
# 💾 Memory Save
# ============================================================
def save_memory(username: str, memory_type: str, content: str, importance: int = 5):
    """एउटा memory सेभ गर्ने (smart duplicate check)"""
    if not content or len(content.strip()) < 5:
        return False

    conn = _get_conn()
    c = conn.cursor()
    now = datetime.now().isoformat()

    # सबै existing memory तान्ने (same type)
    c.execute(
        "SELECT id, content FROM user_memory WHERE username=? AND memory_type=?",
        (username, memory_type)
    )
    existing = c.fetchall()

    new_keys = _extract_key_values(content)   # ✅ नयाँ: email/phone/URL

    for row in existing:
        old_content = row["content"]
        old_keys = _extract_key_values(old_content)

        # ✅ Check 1: Same email/phone/URL भए duplicate मान्ने
        if new_keys and old_keys and (new_keys & old_keys):
            c.execute(
                "UPDATE user_memory SET last_used=?, importance=MAX(importance, ?), content=? WHERE id=?",
                (now, importance, content, row["id"])
            )
            conn.commit()
            conn.close()
            return True

        # Check 2: Word similarity (60%+)
        old_words = set(old_content.lower().split())
        new_words = set(content.lower().split())
        if old_words and new_words:
            overlap = len(old_words & new_words) / max(len(old_words), len(new_words))
            if overlap > 0.6:
                c.execute(
                    "UPDATE user_memory SET last_used=?, importance=MAX(importance, ?), content=? WHERE id=?",
                    (now, importance, content, row["id"])
                )
                conn.commit()
                conn.close()
                return True

    # नयाँ memory insert
    c.execute(
        "INSERT INTO user_memory (username, memory_type, content, importance, created_at, last_used) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (username, memory_type, content, importance, now, now)
    )
    conn.commit()
    conn.close()
    return True


def get_memories(username: str, memory_type: str = None, limit: int = 20) -> list:
    """Memory पढ्ने"""
    conn = _get_conn()
    c = conn.cursor()
    if memory_type:
        c.execute(
            "SELECT * FROM user_memory WHERE username=? AND memory_type=? "
            "ORDER BY importance DESC, last_used DESC LIMIT ?",
            (username, memory_type, limit)
        )
    else:
        c.execute(
            "SELECT * FROM user_memory WHERE username=? "
            "ORDER BY importance DESC, last_used DESC LIMIT ?",
            (username, limit)
        )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_memory_context(username: str, max_items: int = 15) -> str:
    """Agent लाई दिनको लागि formatted memory context"""
    memories = get_memories(username, limit=max_items)
    if not memories:
        return ""
    lines = ["🧠 **तपाईंको पुरानो जानकारी (Memory):**"]
    for m in memories:
        emoji = {"fact": "📌", "preference": "⚙️", "summary": "📝", "profile": "👤"}.get(m["memory_type"], "•")
        lines.append(f"{emoji} {m['content']}")
    return "\n".join(lines)


# ============================================================
# 🤖 Auto-extract memories from conversation
# ============================================================
def extract_memories_from_text(username: str, user_text: str, ai_text: str):
    """Conversation बाट महत्त्वपूर्ण fact/preference निकालेर सेभ गर्ने"""
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        prompt = f"""Analyze this conversation and extract important long-term facts.

USER said: {user_text}
AI answered: {ai_text[:500]}

Extract ONLY these types of info (if present):
1. **fact**: Personal facts (name, age, health condition, email, phone, location)
2. **preference**: How user likes things (language, length, format)
3. **profile**: Profession, interests, goals

⚠️ Rules:
- Return ONLY a JSON array, no other text.
- Each item: {{"type": "fact|preference|profile", "content": "short sentence", "importance": 1-10}}
- If nothing important, return []
- Content in Nepali or English (match user language)
- Max 3 items.

Example output:
[{{"type": "fact", "content": "User's email is test@gmail.com", "importance": 8}}]

JSON:"""
        response = client.models.generate_content(model=MODEL, contents=prompt)
        text = response.text.strip()

        # JSON parse
        text = text.replace("```json", "").replace("```", "").strip()
        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1 or end == 0:
            return 0
        items = json.loads(text[start:end])

        saved = 0
        for item in items:
            if isinstance(item, dict) and "content" in item:
                save_memory(
                    username,
                    item.get("type", "fact"),
                    item["content"],
                    int(item.get("importance", 5))
                )
                saved += 1
        return saved
    except Exception as e:
        print(f"[MEMORY EXTRACT ERROR] {e}")
        return 0


# ============================================================
# 📝 Conversation Summary (हरेक 10 messages पछि)
# ============================================================
def summarize_conversation(username: str, messages: list, force: bool = False):
    """पुरानो कुराकानीको सारांश बनाएर सेभ गर्ने"""
    if not messages or len(messages) < 6:
        return None
    if not force and len(messages) % 10 != 0:
        return None

    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        convo_text = "\n".join([
            f"{m['role']}: {m['content'][:300]}"
            for m in messages[-20:]  # last 20
        ])
        prompt = f"""Summarize this conversation in 3-4 short points (Nepali or English).

{convo_text}

Return only the summary, no preamble."""
        response = client.models.generate_content(model=MODEL, contents=prompt)
        summary = response.text.strip()[:1000]

        conn = _get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO conversation_summary (username, summary, msg_count, created_at) "
            "VALUES (?, ?, ?, ?)",
            (username, summary, len(messages), datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        return summary
    except Exception as e:
        print(f"[SUMMARY ERROR] {e}")
        return None


def get_latest_summary(username: str) -> str:
    """पछिल्लो conversation summary"""
    conn = _get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT summary FROM conversation_summary WHERE username=? "
        "ORDER BY created_at DESC LIMIT 1",
        (username,)
    )
    row = c.fetchone()
    conn.close()
    return row["summary"] if row else ""


# ============================================================
# 🗑️ Memory Management
# ============================================================
def delete_memory(username: str, memory_id: int):
    conn = _get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM user_memory WHERE id=? AND username=?", (memory_id, username))
    conn.commit()
    conn.close()


def clear_all_memories(username: str):
    conn = _get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM user_memory WHERE username=?", (username,))
    c.execute("DELETE FROM conversation_summary WHERE username=?", (username,))
    conn.commit()
    conn.close()