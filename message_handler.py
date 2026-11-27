# message_handler.py — PDF Brain v54.0 (AI Email Reply Generator)
import os
import json
import time
import hashlib
from datetime import datetime, timedelta

from dotenv import load_dotenv
from audit_logger import log_event, get_audit_logs

load_dotenv()

# ============================================================
# Configuration
# ============================================================
MEMORY_DIR = "email_memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

MAX_HISTORY = 10               # प्रति user कति message सम्झने
RATE_LIMIT_WINDOW = 60         # सेकेन्ड
MAX_REPLIES_PER_WINDOW = 3     # एकै window मा कति reply

GEMINI_MODEL = "gemini-2.5-flash-lite"
MAX_BODY_FOR_AI = 1200         # AI लाई कति body पठाउने
MAX_REPLY_LENGTH = 2000        # reply को अधिकतम लम्बाइ


# ============================================================
# User Memory (JSON-based)
# ============================================================
def _user_file(user_id):
    """User ID बाट safe filename बनाउने"""
    safe = hashlib.md5(user_id.lower().strip().encode()).hexdigest()
    return os.path.join(MEMORY_DIR, f"{safe}.json")


def get_user(user_id):
    """User को memory load गर्ने"""
    path = _user_file(user_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "user_id": user_id,
        "created_at": datetime.now().isoformat(),
        "last_seen": datetime.now().isoformat(),
        "history": [],           # list of {role, text, timestamp}
        "preferred_language": "ne",
        "total_messages": 0,
        "last_reply_times": [],  # rate limit tracking
    }


def save_user(user_id, data):
    """User को memory save गर्ने"""
    path = _user_file(user_id)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[MEMORY ERROR] {e}")
        return False


def add_to_history(user_id, role, text):
    """History मा message थप्ने (max limit सहित)"""
    data = get_user(user_id)
    data["history"].append({
        "role": role,
        "text": text[:500],   # truncate
        "timestamp": datetime.now().isoformat()
    })
    # Purane messages hataune
    if len(data["history"]) > MAX_HISTORY * 2:
        data["history"] = data["history"][-MAX_HISTORY * 2:]
    data["total_messages"] = data.get("total_messages", 0) + 1
    data["last_seen"] = datetime.now().isoformat()
    save_user(user_id, data)


# ============================================================
# Rate Limiting
# ============================================================
def _is_rate_limited(user_id):
    """User ले धेरै पटक email पठाएको छ कि जाँच्ने"""
    data = get_user(user_id)
    now = time.time()
    # पुरानो timestamps हटाउने
    recent = [
        t for t in data.get("last_reply_times", [])
        if now - t < RATE_LIMIT_WINDOW
    ]
    if len(recent) >= MAX_REPLIES_PER_WINDOW:
        return True, int(RATE_LIMIT_WINDOW - (now - recent[0]))
    # Update
    recent.append(now)
    data["last_reply_times"] = recent
    save_user(user_id, data)
    return False, 0


# ============================================================
# Intent Detection (Rule-based quick check)
# ============================================================
def _detect_intent(text):
    """सोधाइ को प्रकार पत्ता लगाउने"""
    t = text.lower()

    # Greeting
    if any(k in t for k in ["hello", "hi ", "hey", "namaste", "नमस्ते", "नमस्कार"]):
        if len(text) < 30:
            return "greeting"

    # Thanks
    if any(k in t for k in ["thank", "thanks", "dhanyabad", "धन्यवाद"]):
        return "thanks"

    # Complaint
    if any(k in t for k in ["problem", "issue", "error", "bug", "not working",
                             "समस्या", "त्रुटि", "काम गर्दैन"]):
        return "complaint"

    # Question
    if "?" in text or any(k in t for k in ["how", "what", "why", "when", "where",
                                            "कसरी", "के", "किन", "कहिले", "कहाँ"]):
        return "question"

    # Request
    if any(k in t for k in ["please", "can you", "could you", "help",
                             "कृपया", "सक्नुहुन्छ", "मदत"]):
        return "request"

    return "general"


# ============================================================
# Language Detection (simple heuristic)
# ============================================================
def _detect_language(text):
    """Text को भाषा पत्ता लगाउने (Devanagari vs Latin)"""
    devanagari = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    latin = sum(1 for c in text if c.isalpha() and c.isascii())

    if devanagari > latin:
        # नेपाली vs हिन्दी — केही सामान्य शब्दले छुट्याउने
        if any(k in text for k in ["छ", "हो", "गर्नु", "हुन्छ", "तपाईं"]):
            return "ne"
        return "hi"
    return "en"


# ============================================================
# Gemini AI Reply
# ============================================================
def _ai_generate_reply(user_id, email_body, history, lang="ne"):
    """Gemini बाट intelligent reply बनाउने"""
    try:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None, "GEMINI_API_KEY .env मा छैन"

        client = genai.Client(api_key=api_key)

        # Language instruction
        lang_map = {
            "ne": "तपाईंले अनिवार्य रूपमा नेपालीमा मात्र जवाफ दिनुपर्छ।",
            "hi": "आपको केवल हिन्दी में उत्तर देना चाहिए।",
            "en": "You must reply strictly in English.",
        }
        lang_instruction = lang_map.get(lang, "Reply in the same language as the email.")

        # History context
        history_text = ""
        if history:
            lines = []
            for h in history[-6:]:  # last 6 messages
                role = "User" if h["role"] == "user" else "AI"
                lines.append(f"{role}: {h['text'][:200]}")
            history_text = "\n".join(lines)

        prompt = f"""You are PDF Brain, a helpful AI email assistant.

Your job: Read the email and reply helpfully, professionally, and briefly.

⚠️ RULES:
1. {lang_instruction}
2. Reply in 3-6 sentences (concise).
3. Be polite and professional.
4. If the email asks a question — answer clearly.
5. If it's a complaint — apologize and offer help.
6. If it's a greeting — greet back warmly.
7. Do NOT mention that you are an AI unless asked.
8. Sign as "PDF Brain Team".
9. Use plain text (no markdown).

📧 Email from user:
{email_body[:MAX_BODY_FOR_AI]}

📜 Previous conversation (if any):
{history_text if history_text else "(no previous conversation)"}

✍️ Write the reply now:
"""

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        reply = response.text.strip()
        if not reply:
            return None, "Empty AI response"

        # Length limit
        if len(reply) > MAX_REPLY_LENGTH:
            reply = reply[:MAX_REPLY_LENGTH] + "..."

        return reply, None

    except Exception as e:
        return None, str(e)


# ============================================================
# Fallback Reply (AI fail भए)
# ============================================================
def _fallback_reply(intent, lang="ne"):
    """AI fail भए rule-based reply"""
    templates = {
        "greeting": {
            "ne": "नमस्ते! PDF Brain मा स्वागत छ। तपाईंलाई के सहयोग गर्न सक्छु?",
            "hi": "नमस्ते! PDF Brain में आपका स्वागत है। मैं आपकी कैसे मदद कर सकता हूँ?",
            "en": "Hello! Welcome to PDF Brain. How can I help you today?",
        },
        "thanks": {
            "ne": "धन्यवाद! तपाईंलाई अरु केही चाहिए भने जनाउनुहोस्।",
            "hi": "धन्यवाद! अगर आपको कुछ और चाहिए तो बताएं।",
            "en": "You're welcome! Let me know if you need anything else.",
        },
        "complaint": {
            "ne": "तपाईंको समस्याको लागि क्षमा प्रार्थी छौं। कृपया समस्या विस्तारमा लेख्नुहोस्, हामी चाँडै समाधान गर्नेछौं।",
            "hi": "आपकी समस्या के लिए हम क्षमाप्रार्थी हैं। कृपया समस्या विस्तार से लिखें, हम जल्द समाधान करेंगे।",
            "en": "We apologize for the issue. Please describe it in detail, and we'll resolve it soon.",
        },
        "question": {
            "ne": "तपाईंको प्रश्न प्राप्त भयो। हामी चाँडै विस्तृत जवाफ पठाउनेछौं। कृपया धैर्य गर्नुहोस्।",
            "hi": "आपका प्रश्न प्राप्त हुआ। हम जल्द विस्तृत उत्तर भेजेंगे। कृपया धैर्य रखें।",
            "en": "We received your question. We'll send a detailed answer soon. Please be patient.",
        },
        "request": {
            "ne": "तपाईंको अनुरोध प्राप्त भयो। हामी टिमले चाँडै सम्पर्क गर्नेछ।",
            "hi": "आपका अनुरोध प्राप्त हुआ। हमारी टीम जल्द संपर्क करेगी।",
            "en": "We received your request. Our team will contact you soon.",
        },
        "general": {
            "ne": "तपाईंको email प्राप्त भयो। PDF Brain टिमले चाँडै जवाफ पठाउनेछ। धन्यवाद!",
            "hi": "आपका ईमेल प्राप्त हुआ। PDF Brain टीम जल्द जवाफ भेजेगी। धन्यवाद!",
            "en": "We received your email. The PDF Brain team will reply soon. Thank you!",
        },
    }
    return templates.get(intent, templates["general"]).get(lang, templates["general"]["en"])


# ============================================================
# Main Handler
# ============================================================
def handle_message(user_id, email_body, force_lang=None):
    """
    Email body लाई process गरेर AI reply फर्काउने।
    
    Args:
        user_id: unique user identifier (जस्तै "email_user@example.com")
        email_body: email को text
        force_lang: भाषा force गर्ने (optional)
    
    Returns:
        reply text (str) — खाली string भए skip
    """
    if not email_body or len(email_body.strip()) < 3:
        return ""

    user_id = user_id.lower().strip()

    # 1. Rate limit check
    limited, wait_sec = _is_rate_limited(user_id)
    if limited:
        log_event(
            event_type="rate_limited",
            email=user_id.replace("email_", ""),
            action="email_reply",
            status="blocked",
            details={"wait_seconds": wait_sec}
        )
        print(f"[RATE LIMIT] {user_id} — {wait_sec}s पर्खनुहोस्")
        return ""

    # 2. Language detect
    lang = force_lang or _detect_language(email_body)

    # 3. Intent detect
    intent = _detect_intent(email_body)

    # 4. User memory load
    user_data = get_user(user_id)
    history = user_data.get("history", [])

    # 5. Greeting मा सजिलो reply (AI call नगर्ने)
    if intent == "greeting" and len(email_body) < 30:
        reply = _fallback_reply("greeting", lang)
        add_to_history(user_id, "user", email_body)
        add_to_history(user_id, "ai", reply)
        log_event(
            event_type="email_received",
            email=user_id.replace("email_", ""),
            action="auto_reply",
            status="success",
            details={"intent": "greeting", "lang": lang, "method": "template"}
        )
        return reply

    # 6. Thanks को लागि पनि सजिलो reply
    if intent == "thanks" and len(email_body) < 50:
        reply = _fallback_reply("thanks", lang)
        add_to_history(user_id, "user", email_body)
        add_to_history(user_id, "ai", reply)
        log_event(
            event_type="email_received",
            email=user_id.replace("email_", ""),
            action="auto_reply",
            status="success",
            details={"intent": "thanks", "lang": lang, "method": "template"}
        )
        return reply

    # 7. AI reply
    reply, error = _ai_generate_reply(user_id, email_body, history, lang)

    # 8. AI fail भए fallback
    if not reply:
        print(f"[AI FALLBACK] {user_id}: {error}")
        reply = _fallback_reply(intent, lang)
        method = "fallback"
    else:
        method = "ai"

    # 9. History save
    add_to_history(user_id, "user", email_body)
    add_to_history(user_id, "ai", reply)

    # 10. Audit log
    log_event(
        event_type="email_received",
        email=user_id.replace("email_", ""),
        action="auto_reply",
        status="success" if method == "ai" else "fallback",
        details={
            "intent": intent,
            "lang": lang,
            "method": method,
            "reply_length": len(reply),
            "error": error if method == "fallback" else None,
        }
    )

    return reply


# ============================================================
# Utility: User Profile
# ============================================================
def get_user_profile(user_id):
    """User को profile फर्काउने (Admin Panel का लागि)"""
    data = get_user(user_id)
    return {
        "user_id": data.get("user_id"),
        "total_messages": data.get("total_messages", 0),
        "created_at": data.get("created_at"),
        "last_seen": data.get("last_seen"),
        "preferred_language": data.get("preferred_language", "ne"),
        "history_count": len(data.get("history", [])),
        "recent_history": data.get("history", [])[-5:],
    }


def clear_user_memory(user_id):
    """User को memory clear गर्ने"""
    path = _user_file(user_id)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def list_all_users(limit=50):
    """सबै users को list (Admin का लागि)"""
    users = []
    if not os.path.exists(MEMORY_DIR):
        return users
    for fname in os.listdir(MEMORY_DIR):
        if fname.endswith(".json"):
            path = os.path.join(MEMORY_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                users.append({
                    "user_id": data.get("user_id"),
                    "total_messages": data.get("total_messages", 0),
                    "last_seen": data.get("last_seen"),
                })
            except Exception:
                pass
    users.sort(key=lambda x: x.get("last_seen", ""), reverse=True)
    return users[:limit]


# ============================================================
# CLI Test
# ============================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("🧪 Testing message_handler.py\n")

        test_emails = [
            ("email_test@example.com", "नमस्ते! तपाईंको PDF Brain कस्तो छ?"),
            ("email_test@example.com", "How do I upload a PDF?"),
            ("email_test@example.com", "मेरो PDF process हुँदैन, समस्या छ।"),
            ("email_test@example.com", "धन्यवाद!"),
        ]

        for uid, body in test_emails:
            print(f"{'='*60}")
            print(f"📧 User: {uid}")
            print(f"📝 Body: {body}")
            print(f"{'─'*60}")

            reply = handle_message(uid, body)
            print(f"🤖 Reply: {reply}\n")

            time.sleep(1)  # rate limit avoid

    elif len(sys.argv) > 1 and sys.argv[1] == "profile":
        if len(sys.argv) > 2:
            uid = sys.argv[2]
            profile = get_user_profile(uid)
            print(json.dumps(profile, indent=2, ensure_ascii=False))
        else:
            print("Usage: python message_handler.py profile <user_id>")

    elif len(sys.argv) > 1 and sys.argv[1] == "users":
        users = list_all_users()
        print(f"📊 Total {len(users)} users:\n")
        for u in users:
            print(f"  👤 {u['user_id']} — {u['total_messages']} messages, last: {u['last_seen']}")

    else:
        print("Usage:")
        print("  python message_handler.py test                   — Test replies")
        print("  python message_handler.py profile <user_id>      — User profile")
        print("  python message_handler.py users                  — List all users")