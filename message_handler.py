# message_handler.py — Shared logic for Email + WhatsApp
import os
import re
import json
from datetime import datetime
from answer import answer_question
from tags import get_all_tags, get_pdfs_by_tags

# ============================================================
# User Data Storage
# ============================================================
USERS_DATA_FILE = "messaging_users.json"


def load_users_data():
    """Users को conversation + preferences"""
    if not os.path.exists(USERS_DATA_FILE):
        return {}
    try:
        with open(USERS_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_users_data(data):
    """Save users data"""
    try:
        with open(USERS_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def get_user(user_id):
    """User को data लिने (वा नयाँ बनाउने)"""
    users = load_users_data()
    
    if user_id not in users:
        users[user_id] = {
            "created": datetime.now().isoformat(),
            "language": "ne",
            "history": [],          # Last 5 conversations
            "stats": {
                "queries": 0,
                "feedback_positive": 0,
                "feedback_negative": 0
            },
            "tag_filter": []
        }
        save_users_data(users)
    
    return users[user_id]


def update_user(user_id, updates):
    """User data update गर्ने"""
    users = load_users_data()
    if user_id not in users:
        users[user_id] = get_user(user_id)
    
    for key, val in updates.items():
        users[user_id][key] = val
    
    save_users_data(users)


def add_to_history(user_id, role, content):
    """Conversation history मा थप्ने"""
    users = load_users_data()
    if user_id not in users:
        get_user(user_id)
        users = load_users_data()
    
    if "history" not in users[user_id]:
        users[user_id]["history"] = []
    
    users[user_id]["history"].append({
        "role": role,
        "content": content[:500],
        "time": datetime.now().isoformat()
    })
    
    # Last 10 मात्र राख्ने
    users[user_id]["history"] = users[user_id]["history"][-10:]
    
    save_users_data(users)


# ============================================================
# Language Support
# ============================================================
MESSAGES = {
    "ne": {
        "welcome": "🧠 *PDF Brain* मा स्वागत!\n\nमलाई PDF बारे जे पनि सोध्नुहोस्।",
        "help": """📚 *PDF Brain Help*

*Commands:*
• `hi` — स्वागत
• `help` — यो help
• `stats` — तपाईंको stats
• `list` — PDF list
• `tags` — सबै tags
• `tag:XYZ प्रश्न` — tag filter
• `lang ne/en/hi` — भाषा फेर्ने
• `clear` — history मेट्ने

*प्रश्न सोध्ने:*
सिधै नेपालीमा सोध्नुहोस्।""",
        "stats": "📊 *तपाईंको Stats*",
        "thinking": "🤔 सोच्दै...",
        "not_found": "मलाई यो जानकारी भेटिएन।",
        "error": "❌ केही गडबड भयो। फेरि try गर्नुहोस्।",
        "feedback_q": "जवाफ कस्तो लाग्यो? 👍 वा 👎",
        "feedback_thanks": "✅ धन्यवाद!",
        "cleared": "✅ History मेटियो",
        "no_pdfs": "कुनै PDF छैन",
        "tag_set": "🏷️ Tag filter लगाइयो:",
        "tag_cleared": "✅ Tag filter हटाइयो",
        "lang_changed": "✅ भाषा फेरियो: नेपाली"
    },
    "en": {
        "welcome": "🧠 Welcome to *PDF Brain*!\n\nAsk me anything about your PDFs.",
        "help": """📚 *PDF Brain Help*

*Commands:*
• `hi` — Welcome
• `help` — This help
• `stats` — Your stats
• `list` — PDF list
• `tags` — All tags
• `tag:XYZ question` — Tag filter
• `lang ne/en/hi` — Change language
• `clear` — Clear history

*Ask questions:*
Just type in English.""",
        "stats": "📊 *Your Stats*",
        "thinking": "🤔 Thinking...",
        "not_found": "I couldn't find this information.",
        "error": "❌ Something went wrong. Try again.",
        "feedback_q": "How was the answer? 👍 or 👎",
        "feedback_thanks": "✅ Thanks!",
        "cleared": "✅ History cleared",
        "no_pdfs": "No PDFs available",
        "tag_set": "🏷️ Tag filter set:",
        "tag_cleared": "✅ Tag filter removed",
        "lang_changed": "✅ Language changed: English"
    },
    "hi": {
        "welcome": "🧠 *PDF Brain* में स्वागत!\n\nPDF के बारे में कुछ भी पूछें।",
        "help": """📚 *PDF Brain Help*

*Commands:*
• `hi` — Welcome
• `help` — Help
• `stats` — आपके stats
• `list` — PDF list
• `tags` — सभी tags
• `tag:XYZ प्रश्न` — Tag filter
• `lang ne/en/hi` — भाषा बदलें
• `clear` — History साफ

*प्रश्न पूछें:*
सीधे टाइप करें।""",
        "stats": "📊 *आपके Stats*",
        "thinking": "🤔 सोच रहा हूँ...",
        "not_found": "यह जानकारी नहीं मिली।",
        "error": "❌ कुछ गड़बड़ हुई। फिर try करें।",
        "feedback_q": "जवाफ कैसा लगा? 👍 या 👎",
        "feedback_thanks": "✅ धन्यवाद!",
        "cleared": "✅ History साफ",
        "no_pdfs": "कोई PDF नहीं",
        "tag_set": "🏷️ Tag filter लगाया:",
        "tag_cleared": "✅ Tag filter हटाया",
        "lang_changed": "✅ भाषा बदली: हिन्दी"
    }
}


def msg(user_id, key):
    """User को भाषा अनुसार message"""
    user = get_user(user_id)
    lang = user.get("language", "ne")
    return MESSAGES.get(lang, MESSAGES["ne"]).get(key, key)


# ============================================================
# Command Parser
# ============================================================
def parse_command(message, user_id):
    """
    Message parse गर्ने — command हो कि प्रश्न?
    Returns: (type, data)
    """
    text = message.strip()
    text_lower = text.lower()
    
    # Greeting
    if text_lower in ["hi", "hello", "hey", "नमस्ते", "namaste", "नमस्कार"]:
        return "greeting", None
    
    # Help
    if text_lower in ["help", "सहयोग", "मदत", "?"]:
        return "help", None
    
    # Stats
    if text_lower in ["stats", "statistics", "तथ्याङ्क", "आँकडा"]:
        return "stats", None
    
    # List PDFs
    if text_lower in ["list", "pdfs", "pdf list", "सूची"]:
        return "list", None
    
    # Tags
    if text_lower in ["tags", "tag list", "ट्याग"]:
        return "tags", None
    
    # Clear
    if text_lower in ["clear", "reset", "साफ"]:
        return "clear", None
    
    # Language
    lang_match = re.match(r'lang\s+(ne|en|hi|nepali|english|hindi)', text_lower)
    if lang_match:
        lang_map = {
            "ne": "ne", "nepali": "ne",
            "en": "en", "english": "en",
            "hi": "hi", "hindi": "hi"
        }
        return "lang", lang_map.get(lang_match.group(1), "ne")
    
    # Tag filter — tag:financial प्रश्न
    tag_match = re.match(r'tag:([a-zA-Z0-9_,]+)\s+(.+)', text)
    if tag_match:
        tags = [t.strip().lower() for t in tag_match.group(1).split(",")]
        question = tag_match.group(2).strip()
        return "query_with_tag", {"tags": tags, "question": question}
    
    # Feedback — emoji + text (flexible)
    text_stripped = text.strip()
    text_lower_check = text_stripped.lower()
    
    # Positive
    if any(kw in text_stripped or kw in text_lower_check for kw in [
        "👍", "like", "good", "ramro", "राम्रो", "thik", "ठीक", "sahi", "सही"
    ]):
        return "feedback", "positive"
    
    # Negative
    if any(kw in text_stripped or kw in text_lower_check for kw in [
        "👎", "dislike", "bad", "naramro", "नराम्रो", "kharab", "खराब"
    ]):
        return "feedback", "negative"
    
    # Default: query
    return "query", text


# ============================================================
# Command Handlers
# ============================================================
def handle_greeting(user_id):
    """Greeting response"""
    user = get_user(user_id)
    queries = user.get("stats", {}).get("queries", 0)
    
    if queries > 0:
        return f"{msg(user_id, 'welcome')}\n\n📊 अहिलेसम्म: *{queries}* queries"
    return msg(user_id, "welcome")


def handle_help(user_id):
    """Help menu"""
    return msg(user_id, "help")


def handle_stats(user_id):
    """User को stats"""
    user = get_user(user_id)
    stats = user.get("stats", {})
    
    total = stats.get("queries", 0)
    pos = stats.get("feedback_positive", 0)
    neg = stats.get("feedback_negative", 0)
    
    created = user.get("created", "")
    if created:
        try:
            created_dt = datetime.fromisoformat(created)
            days = (datetime.now() - created_dt).days
            member_since = f"{days} दिन"
        except Exception:
            member_since = "?"
    else:
        member_since = "?"
    
    # Language emoji
    lang_emoji = {"ne": "🇳🇵", "en": "🇬🇧", "hi": "🇮🇳"}
    lang = user.get("language", "ne")
    
    text = f"""📊 *तपाईंको Stats*

💬 Total Queries: *{total}*
👍 Positive: *{pos}*
👎 Negative: *{neg}*
📅 Member: *{member_since}*
{lang_emoji.get(lang, '🌐')} Language: *{lang.upper()}*"""

    # Tag filter
    if user.get("tag_filter"):
        text += f"\n🏷️ Active Filter: *{', '.join(user['tag_filter'])}*"
    
    return text


def handle_list_pdfs(user_id):
    """PDF list"""
    if not os.path.exists("docs"):
        return msg(user_id, "no_pdfs")
    
    pdfs = [f for f in os.listdir("docs") if f.lower().endswith(".pdf")]
    if not pdfs:
        return msg(user_id, "no_pdfs")
    
    text = f"📚 *{len(pdfs)} PDFs:*\n\n"
    for i, pdf in enumerate(pdfs[:20], 1):
        # Tag थप्ने
        try:
            from tags import get_pdf_tags
            tags = get_pdf_tags(pdf)
            tag_str = f" 🏷️ {', '.join(tags)}" if tags else ""
        except Exception:
            tag_str = ""
        
        # नाम छोटो
        name = pdf if len(pdf) < 40 else pdf[:37] + "..."
        text += f"{i}. {name}{tag_str}\n"
    
    if len(pdfs) > 20:
        text += f"\n... अरू {len(pdfs) - 20} PDFs"
    
    return text


def handle_tags(user_id):
    """सबै tags देखाउने"""
    try:
        all_tags = get_all_tags()
        if not all_tags:
            return "🏷️ कुनै tag छैन"
        
        text = f"🏷️ *{len(all_tags)} Tags:*\n\n"
        for tag in all_tags:
            try:
                pdfs = get_pdfs_by_tags([tag])
                text += f"• *{tag}* — {len(pdfs)} PDFs\n"
            except Exception:
                text += f"• *{tag}*\n"
        
        text += f"\n💡 _Usage:_ `tag:{all_tags[0]} तपाईंको प्रश्न`"
        return text
    except Exception:
        return "🏷️ Tags load गर्न सकिएन"


def handle_clear(user_id):
    """History मेट्ने"""
    update_user(user_id, {"history": [], "tag_filter": []})
    return msg(user_id, "cleared")


def handle_lang(user_id, new_lang):
    """Language फेर्ने"""
    update_user(user_id, {"language": new_lang})
    
    lang_names = {"ne": "नेपाली", "en": "English", "hi": "हिन्दी"}
    return f"✅ भाषा फेरियो: *{lang_names.get(new_lang, new_lang)}*"


def handle_feedback(user_id, feedback_type):
    """Feedback save"""
    users = load_users_data()
    if user_id not in users:
        get_user(user_id)
        users = load_users_data()
    
    stats = users[user_id].get("stats", {})
    if feedback_type == "positive":
        stats["feedback_positive"] = stats.get("feedback_positive", 0) + 1
    else:
        stats["feedback_negative"] = stats.get("feedback_negative", 0) + 1
    
    users[user_id]["stats"] = stats
    save_users_data(users)
    
    return msg(user_id, "feedback_thanks")


def handle_query(user_id, question, tag_filter=None):
    """Query process"""
    # User को tag filter प्रयोग गर्ने
    if not tag_filter:
        user = get_user(user_id)
        tag_filter = user.get("tag_filter") or None
    
    try:
        result = answer_question(
            question,
            username=f"msg_{user_id}",
            tag_filter=tag_filter
        )
        
        answer = result["answer"]
        sources = result.get("sources", [])
        
        # Stats update
        users = load_users_data()
        if user_id not in users:
            get_user(user_id)
            users = load_users_data()
        users[user_id]["stats"]["queries"] = users[user_id]["stats"].get("queries", 0) + 1
        save_users_data(users)
        
        # History update
        add_to_history(user_id, "user", question)
        add_to_history(user_id, "assistant", answer)
        
        # Sources थप्ने
        if sources:
            answer += f"\n\n📚 _स्रोत:_"
            for s in sources[:3]:
                answer += f"\n• {s}"
        
        # Feedback prompt
        answer += f"\n\n_{msg(user_id, 'feedback_q')}_"
        
        return answer
    
    except Exception as e:
        return f"{msg(user_id, 'error')}\n\n`{str(e)[:100]}`"


# ============================================================
# Main Handler — सबै Messages यहाँबाट
# ============================================================
def handle_message(user_id, message):
    """
    सबै messages यहाँबाट process हुन्छन्।
    Email + WhatsApp दुवैले यही function प्रयोग गर्छन्।
    """
    if not message or not message.strip():
        return None
    
    # Command parse
    cmd_type, data = parse_command(message, user_id)
    
    # Route
    if cmd_type == "greeting":
        return handle_greeting(user_id)
    elif cmd_type == "help":
        return handle_help(user_id)
    elif cmd_type == "stats":
        return handle_stats(user_id)
    elif cmd_type == "list":
        return handle_list_pdfs(user_id)
    elif cmd_type == "tags":
        return handle_tags(user_id)
    elif cmd_type == "clear":
        return handle_clear(user_id)
    elif cmd_type == "lang":
        return handle_lang(user_id, data)
    elif cmd_type == "feedback":
        return handle_feedback(user_id, data)
    elif cmd_type == "query_with_tag":
        return handle_query(user_id, data["question"], tag_filter=data["tags"])
    elif cmd_type == "query":
        return handle_query(user_id, data)
    else:
        return msg(user_id, "error")


# ============================================================
# Test
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🧪 message_handler.py Test")
    print("=" * 60 + "\n")
    
    test_user = "test_user_123"
    
    # Test messages
    tests = [
        "hi",
        "help",
        "stats",
        "list",
        "tags",
        "यो document कसको हो?",
        "👍",
        "lang en",
        "stats",
        "lang ne",
        "tag:financial कति amount छ?"
    ]
    
    for msg_text in tests:
        print(f"\n{C if False else ''}👤 User: {msg_text}")
        response = handle_message(test_user, msg_text)
        if response:
            print(f"🧠 Bot: {response[:200]}...")
        else:
            print("🧠 Bot: (empty)")
        print("-" * 60)