# spam_filter.py — PDF Brain AI Spam Filter
import os
import re
import json
import hashlib
from datetime import datetime

# ============================================================
# Rule-based keywords (fast pre-filter)
# ============================================================
SKIP_SENDER_KEYWORDS = [
    "no-reply", "noreply", "do_not_reply", "donotreply", "do-not-reply",
    "notification", "newsletter", "marketing", "promo",
    "info@", "support@", "bounce", "mailer", "auto-confirm",
    "binance", "coinbase", "kraken", "facebookmail", "linkedin",
    "twitter", "instagram", "youtube", "google-noreply",
    "microsoft", "apple", "amazon", "verify", "confirm",
    "security", "no_reply", "alert"
]

SKIP_SUBJECT_KEYWORDS = [
    "unsubscribe", "verify your", "confirm your", "security alert",
    "suspicious", "password reset", "new login", "login attempt",
    "order confirmed", "shipping", "delivery", "newsletter",
    "weekly", "daily digest", "promotion", "offer", "sale",
    "discount", "your receipt", "your invoice", "your statement",
    "bitcoin", "crypto", "investment", "earn more"
]


# ============================================================
# Cache — AI लाई बारम्बार नसोध्न
# ============================================================
SPAM_CACHE_FILE = "spam_cache.json"


def _load_cache():
    if os.path.exists(SPAM_CACHE_FILE):
        try:
            with open(SPAM_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_cache(cache):
    try:
        with open(SPAM_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _cache_key(sender, subject):
    raw = f"{sender.lower()}|{subject.lower()}"
    return hashlib.md5(raw.encode()).hexdigest()


# ============================================================
# AI Spam Detection (Gemini)
# ============================================================
def _ai_is_spam(sender, subject, body_preview=""):
    """Gemini लाई सोध्ने — spam हो कि होइन"""
    try:
        from google import genai
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None, "No GEMINI_API_KEY"

        client = genai.Client(api_key=api_key)
        MODEL = "gemini-2.5-flash-lite"

        prompt = f"""You are an email spam classifier.

Classify this email as SPAM or HAM (not spam).
Consider: promotional, phishing, automated notifications, marketing, crypto/investment spam.

Sender: {sender}
Subject: {subject}
Body preview: {body_preview[:400]}

Reply ONLY in this JSON format:
{{"classification": "SPAM" or "HAM", "confidence": 0.0-1.0, "reason": "short reason"}}
"""

        response = client.models.generate_content(model=MODEL, contents=prompt)
        text = response.text.strip()

        # JSON निकाल्ने
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            data = json.loads(m.group())
            return data, None
        return None, "AI response parse failed"
    except Exception as e:
        return None, str(e)


# ============================================================
# Main function
# ============================================================
def is_spam(sender_email, subject, body_preview="", use_ai=True):
    """
    Spam check — rule-based + optional AI.
    
    Returns: (is_spam: bool, reason: str, confidence: float, method: str)
    """
    sender_lower = (sender_email or "").lower()
    subject_lower = (subject or "").lower()

    # 1. Rule-based sender check
    for kw in SKIP_SENDER_KEYWORDS:
        if kw in sender_lower:
            return True, f"sender contains '{kw}'", 0.95, "rule"

    # 2. Rule-based subject check
    for kw in SKIP_SUBJECT_KEYWORDS:
        if kw in subject_lower:
            return True, f"subject contains '{kw}'", 0.90, "rule"

    # 3. System email
    if sender_lower.endswith("@mail.gmail.com"):
        return True, "system email", 0.99, "rule"

    # 4. AI check (cache सहित)
    if use_ai:
        cache = _load_cache()
        key = _cache_key(sender_email, subject)

        if key in cache:
            cached = cache[key]
            return (cached["is_spam"], cached["reason"],
                    cached["confidence"], "ai-cache")

        ai_result, err = _ai_is_spam(sender_email, subject, body_preview)
        if ai_result:
            is_spam_val = ai_result.get("classification", "").upper() == "SPAM"
            confidence = float(ai_result.get("confidence", 0.0))
            reason = ai_result.get("reason", "AI classification")

            # Cache save (केवल high confidence)
            if confidence >= 0.7:
                cache[key] = {
                    "is_spam": is_spam_val,
                    "reason": reason,
                    "confidence": confidence,
                    "cached_at": datetime.now().isoformat(),
                }
                # Cache size limit
                if len(cache) > 500:
                    oldest = sorted(cache.items(), key=lambda x: x[1].get("cached_at", ""))[:100]
                    for k, _ in oldest:
                        del cache[k]
                _save_cache(cache)

            return is_spam_val, reason, confidence, "ai"
        else:
            # AI fail — rule-based fallback
            print(f"[SPAM] AI fail: {err}")

    return False, "", 0.0, "none"


def clear_spam_cache():
    """Cache clear गर्ने (admin का लागि)"""
    if os.path.exists(SPAM_CACHE_FILE):
        os.remove(SPAM_CACHE_FILE)
        return True
    return False