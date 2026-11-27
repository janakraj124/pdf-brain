# auth.py — PDF Brain (Secure Auth System v5 — Full 21 Languages + OTP + Reset)
import os
import json
import bcrypt
import re
import secrets
from datetime import datetime, timedelta

USERS_FILE = "users.json"
RESET_TOKEN_FILE = "reset_tokens.json"
OTP_FILE = "reset_otp.json"


# ============================================================
# FILE HELPERS
# ============================================================
def _load_users():
    """Users file पढ्ने; नभए Streamlit Secrets बाट सुरक्षित Bootstrap Admin बनाउने."""
    if not os.path.exists(USERS_FILE):
        bootstrap_user = ""
        bootstrap_pass = ""
        bootstrap_email = ""

        try:
            import streamlit as st
            bootstrap_user = str(st.secrets.get("BOOTSTRAP_ADMIN_USERNAME", "")).strip()
            bootstrap_pass = str(st.secrets.get("BOOTSTRAP_ADMIN_PASSWORD", "")).strip()
            bootstrap_email = str(st.secrets.get("BOOTSTRAP_ADMIN_EMAIL", "")).strip()
        except Exception as e:
            print(f"[BOOTSTRAP SECRETS WARNING] {e}")

        if not bootstrap_user or not bootstrap_pass:
            raise RuntimeError(
                "Users database भेटिएन र Bootstrap Admin Secrets पनि उपलब्ध छैनन्। "
                "Streamlit Secrets मा BOOTSTRAP_ADMIN_USERNAME र "
                "BOOTSTRAP_ADMIN_PASSWORD सेट गर्नुहोस्।"
            )

        print(f"Bootstrap admin account सिर्जना हुँदैछ: {bootstrap_user}")
        default = {
            bootstrap_user: {
                "password": bcrypt.hashpw(
                    bootstrap_pass.encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8"),
                "role": "admin",
                "email": bootstrap_email,
                "created": datetime.now().isoformat(),
                "last_login": None,
                "login_count": 0,
                "failed_attempts": 0,
                "locked_until": None,
                "preferred_language": "ne",
                "profile": {"name": "Admin", "phone": ""}
            }
        }

        if not _save_users(default):
            raise RuntimeError("Bootstrap Admin database save गर्न सकिएन।")
        return default

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
        if not isinstance(users, dict):
            print("[LOAD ERROR] users.json को format गलत छ (JSON object चाहिन्छ)।")
            return {}
        return users
    except Exception as e:
        print(f"[LOAD ERROR] {e}")
        return {}


def _save_users(users):
    """Users JSON file save गर्ने."""
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[SAVE ERROR] {e}")
        return False


def _load_json(filepath):
    """Generic JSON load."""
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"[JSON LOAD ERROR] {filepath}: {e}")
        return {}


def _save_json(filepath, data):
    """Generic JSON save."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[SAVE ERROR] {filepath}: {e}")
        return False


# ============================================================
# LANGUAGE NORMALIZER — सबै २१ भाषा Support
# ============================================================
def _normalize_language(language, default="ne"):
    """
    Translations मा उपलब्ध २१ भाषा मध्ये एउटा normalize गर्ने।
    - Input: "en", "en-US", "EN", "ne_NP", "zh-CN", आदि
    - Output: supported code (जस्तै "en", "ne", "zh")
    - Fallback: default (ne) → en → ne
    """
    # Default languages list (translations import fail भए fallback)
    DEFAULT_SUPPORTED = {
        "en", "ne", "hi", "zh", "es", "fr", "ar", "ja", "ko", "de",
        "pt", "ru", "it", "tr", "id", "vi", "th", "nl", "pl", "sv", "tl"
    }

    # Supported languages लोड गर्ने (translations बाट)
    supported = DEFAULT_SUPPORTED
    try:
        from translations import LANGUAGES
        if LANGUAGES:
            supported = set(LANGUAGES.keys())
    except Exception as e:
        print(f"[LANGUAGE CHECK WARNING] {e} — default list प्रयोग हुँदैछ")

    # Input normalize
    code = str(language or default).strip().lower()
    code = code.replace("_", "-").split("-")[0]

    if code in supported:
        return code

    # Fallback 1: user को default
    fallback = str(default or "ne").strip().lower()
    fallback = fallback.replace("_", "-").split("-")[0]
    if fallback in supported:
        return fallback

    # Fallback 2: en (यदि छ भने)
    if "en" in supported:
        return "en"

    # Fallback 3: ne (यदि छ भने)
    if "ne" in supported:
        return "ne"

    # Final fallback: पहिलो available
    return next(iter(supported), "ne")


def get_supported_languages():
    """सबै supported language codes फर्काउने (UI dropdown का लागि)."""
    try:
        from translations import LANGUAGES
        return list(LANGUAGES.keys())
    except Exception:
        return ["en", "ne", "hi", "zh", "es", "fr", "ar", "ja", "ko",
                "de", "pt", "ru", "it", "tr", "id", "vi", "th", "nl",
                "pl", "sv", "tl"]


def is_language_supported(language):
    """भाषा supported छ कि छैन जाँच्ने."""
    code = str(language or "").strip().lower().replace("_", "-").split("-")[0]
    return code in get_supported_languages()


# ============================================================
# VALIDATION
# ============================================================
def validate_email(email):
    """Email format जाँच."""
    if not email:
        return True
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))


def validate_username(username):
    """Username format जाँच."""
    username = str(username or "")
    if len(username) < 3:
        return False, "Username कम्तिमा ३ अक्षर"
    if len(username) > 20:
        return False, "Username अधिकतम २० अक्षर"
    if not re.match(r'^[\w]+$', username):
        return False, "Username: अक्षर, अंक, _ मात्र"
    return True, "OK"


def check_password_strength(password):
    """Password strength (0-5)."""
    password = str(password or "")
    score = 0
    if len(password) >= 8:
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.islower() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        score += 1
    return score


# ============================================================
# USER MANAGEMENT
# ============================================================
def create_user(username, password, email="", role="user", preferred_language="ne"):
    """नयाँ सामान्य user बनाउने; बाहिरबाट पठाएको role लाई स्वीकार नगर्ने."""
    users = _load_users()

    username = str(username or "").strip()
    password = str(password or "")
    email = str(email or "").strip()

    valid, msg = validate_username(username)
    if not valid:
        return False, msg

    if username in users:
        return False, "Username पहिले नै छ"

    if len(password) < 6:
        return False, "Password कम्तिमा ६ अक्षर"

    if email and not validate_email(email):
        return False, "Email format गलत"

    if email:
        for existing_username, data in users.items():
            if str(data.get("email", "")).lower() == email.lower():
                return False, "Email पहिले नै प्रयोग भएको छ"

    users[username] = {
        "password": bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
        "role": "user",
        "email": email,
        "created": datetime.now().isoformat(),
        "last_login": None,
        "login_count": 0,
        "failed_attempts": 0,
        "locked_until": None,
        "preferred_language": _normalize_language(preferred_language),
        "profile": {"name": username, "phone": ""}
    }

    if not _save_users(users):
        return False, "User save हुन सकेन"
    return True, "User सफलतापूर्वक बन्यो"


def verify_user(username, password):
    """Login verify गर्ने."""
    users = _load_users()
    username = str(username or "").strip()
    password = str(password or "")

    if username not in users:
        # Email बाट पनि खोज्ने
        for u, data in users.items():
            if str(data.get("email", "")).lower() == username.lower():
                username = u
                break
        else:
            return False, {}

    user = users[username]

    locked_until = user.get("locked_until")
    if locked_until:
        try:
            if datetime.now() < datetime.fromisoformat(locked_until):
                return False, {"locked": True, "until": locked_until}
            users[username]["locked_until"] = None
            users[username]["failed_attempts"] = 0
            _save_users(users)
        except (ValueError, TypeError):
            users[username]["locked_until"] = None
            users[username]["failed_attempts"] = 0

    try:
        stored_hash = user.get("password", "")
        if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
            preferred_language = _normalize_language(
                user.get("preferred_language", "ne")
            )
            users[username]["preferred_language"] = preferred_language
            users[username]["last_login"] = datetime.now().isoformat()
            users[username]["login_count"] = user.get("login_count", 0) + 1
            users[username]["failed_attempts"] = 0
            users[username]["locked_until"] = None

            if not _save_users(users):
                print("[AUTH WARNING] Login details database मा save भएन।")

            return True, {
                "username": username,
                "role": user.get("role", "user"),
                "email": user.get("email", ""),
                "profile": user.get("profile", {}),
                "last_login": users[username]["last_login"],
                "login_count": users[username]["login_count"],
                "preferred_language": preferred_language
            }

        users[username]["failed_attempts"] = user.get("failed_attempts", 0) + 1
        if users[username]["failed_attempts"] >= 5:
            users[username]["locked_until"] = (
                datetime.now() + timedelta(minutes=5)
            ).isoformat()
        _save_users(users)
        return False, {
            "failed": True,
            "attempts": users[username]["failed_attempts"]
        }

    except Exception as e:
        print(f"[AUTH ERROR] {e}")
        return False, {}


def update_user_profile(username, name="", email="", phone=""):
    """User profile update."""
    users = _load_users()
    if username not in users:
        return False, "User छैन"

    email = str(email or "").strip()
    if email and not validate_email(email):
        return False, "Email format गलत"

    if email:
        for other_username, data in users.items():
            if other_username != username and str(data.get("email", "")).lower() == email.lower():
                return False, "Email पहिले नै प्रयोग भएको छ"
        users[username]["email"] = email

    if name:
        users[username].setdefault("profile", {})
        users[username]["profile"]["name"] = name
    if phone:
        users[username].setdefault("profile", {})
        users[username]["profile"]["phone"] = phone

    if not _save_users(users):
        return False, "Profile save हुन सकेन"
    return True, "Profile update भयो"


def change_password(username, old_password, new_password):
    """पुरानो password verify गरेर password परिवर्तन."""
    users = _load_users()
    if username not in users:
        return False, "User छैन"

    try:
        if not bcrypt.checkpw(
            str(old_password).encode("utf-8"),
            users[username]["password"].encode("utf-8")
        ):
            return False, "पुरानो password गलत"
    except Exception as e:
        return False, f"Error: {e}"

    new_password = str(new_password or "")
    if len(new_password) < 6:
        return False, "नयाँ password कम्तिमा ६ अक्षर"

    users[username]["password"] = bcrypt.hashpw(
        new_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    if not _save_users(users):
        return False, "Password save हुन सकेन"
    return True, "Password फेरियो"


def reset_password(username, new_password):
    """Admin workflow बाट password reset (caller मा Admin authorization अनिवार्य)."""
    users = _load_users()
    if username not in users:
        return False, "User छैन"

    new_password = str(new_password or "")
    if len(new_password) < 6:
        return False, "Password कम्तिमा ६ अक्षर"

    users[username]["password"] = bcrypt.hashpw(
        new_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    users[username]["failed_attempts"] = 0
    users[username]["locked_until"] = None

    if not _save_users(users):
        return False, "Password reset save हुन सकेन"
    return True, "Password reset भयो"


def update_user_role(username, new_role):
    """Role change helper; caller ले Admin authorization जाँच गर्नैपर्छ."""
    users = _load_users()
    if username not in users:
        return False, "User छैन"
    if new_role not in ["user", "manager", "admin"]:
        return False, "Invalid role"

    users[username]["role"] = new_role
    if not _save_users(users):
        return False, "Role save हुन सकेन"
    return True, f"Role → {new_role}"


# ============================================================
# 🆕 EMAIL-BASED PASSWORD RESET (login.py का लागि)
# ============================================================
def user_exists_by_email(email):
    """
    Email पहिले नै दर्ता छ कि छैन check गर्छ।
    Returns: bool
    """
    email = str(email or "").strip().lower()
    if not email:
        return False

    try:
        users = _load_users()
        for uname, udata in users.items():
            if not isinstance(udata, dict):
                continue
            if str(udata.get("email", "")).strip().lower() == email:
                return True
        return False
    except Exception as e:
        print(f"[auth] user_exists_by_email error: {e}")
        return False


def update_user_password(email, new_password):
    """
    Email द्वारा user खोजेर password update गर्छ (bcrypt सहित)।
    Returns: (success: bool, message: str)
    """
    email = str(email or "").strip().lower()
    new_password = str(new_password or "")

    if not email:
        return False, "Email आवश्यक छ।"
    if not new_password:
        return False, "Password आवश्यक छ।"
    if len(new_password) < 6:
        return False, "Password कम्तिमा ६ अक्षर हुनुपर्छ।"
    if not validate_email(email):
        return False, "Email format गलत छ।"

    try:
        users = _load_users()
        for uname, udata in users.items():
            if not isinstance(udata, dict):
                continue
            if str(udata.get("email", "")).strip().lower() == email:
                # Password update (bcrypt hash)
                users[uname]["password"] = bcrypt.hashpw(
                    new_password.encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8")

                # Lockout reset
                users[uname]["failed_attempts"] = 0
                users[uname]["locked_until"] = None

                if not _save_users(users):
                    return False, "Password save हुन सकेन।"

                return True, f"Password सफलतापूर्वक बदलियो ({uname})।"

        return False, "यो Email दर्ता छैन।"
    except Exception as e:
        return False, f"Password update error: {e}"


def find_user_by_email(email):
    """Email बाट username खोज्ने."""
    email = str(email or "").strip().lower()
    users = _load_users()
    for username, data in users.items():
        if str(data.get("email", "")).lower() == email:
            return username
    return None


# ============================================================
# LIST & STATS
# ============================================================
def list_users():
    """सबै users list (stats र language सहित)."""
    users = _load_users()
    result = []
    for u, data in users.items():
        result.append({
            "username": u,
            "role": data.get("role", "user"),
            "email": data.get("email", ""),
            "preferred_language": _normalize_language(data.get("preferred_language", "ne")),
            "created": data.get("created", ""),
            "last_login": data.get("last_login", ""),
            "login_count": data.get("login_count", 0),
            "failed_attempts": data.get("failed_attempts", 0),
            "locked": bool(data.get("locked_until"))
        })
    return result


def get_user_info(username):
    """एक user को पूरा info (password बिना)."""
    users = _load_users()
    if username not in users:
        return None
    data = users[username].copy()
    data.pop("password", None)
    data["username"] = username
    data["preferred_language"] = _normalize_language(data.get("preferred_language", "ne"))
    return data


def get_user_language(username, default="ne"):
    """प्रयोगकर्ताको सुरक्षित भाषा प्राप्त गर्ने; पुरानो Account migrate गर्ने."""
    users = _load_users()
    if username not in users:
        return _normalize_language(default)

    language = _normalize_language(
        users[username].get("preferred_language", default), default
    )
    if users[username].get("preferred_language") != language:
        users[username]["preferred_language"] = language
        _save_users(users)
    return language


def update_user_language(username, language):
    """
    प्रयोगकर्ताको भाषा परिवर्तन गरेर सुरक्षित गर्ने।
    Returns: (success: bool, message: str)
    """
    users = _load_users()
    if username not in users:
        return False, "User छैन"

    language = _normalize_language(language)
    users[username]["preferred_language"] = language

    if not _save_users(users):
        return False, "Language save हुन सकेन"
    return True, f"Language update भयो: {language}"


def delete_user(username):
    """User हटाउने; admin account हटाउन नदिने."""
    users = _load_users()
    if username in users and users[username].get("role") != "admin":
        del users[username]
        if _save_users(users):
            return True
    return False


def unlock_user(username):
    """Locked user unlock."""
    users = _load_users()
    if username in users:
        users[username]["locked_until"] = None
        users[username]["failed_attempts"] = 0
        return _save_users(users)
    return False


# ============================================================
# TOKEN-BASED RESET (Link)
# ============================================================
def _load_tokens():
    return _load_json(RESET_TOKEN_FILE)


def _save_tokens(tokens):
    return _save_json(RESET_TOKEN_FILE, tokens)


def generate_reset_token(username, email=None):
    """Password reset token (१ घण्टा valid)."""
    users = _load_users()
    if username not in users:
        return None, "User भेटिएन"

    user_email = str(email or users[username].get("email", "")).strip()
    if not user_email:
        return None, "User को email छैन"
    if user_email.lower() != str(users[username].get("email", "")).lower():
        return None, "Account email मिलेन"

    token = secrets.token_urlsafe(32)
    expiry = (datetime.now() + timedelta(hours=1)).isoformat()

    tokens = _load_tokens()
    tokens = {k: v for k, v in tokens.items() if v.get("username") != username}
    tokens[token] = {
        "username": username,
        "email": user_email,
        "expiry": expiry,
        "used": False
    }
    if not _save_tokens(tokens):
        return None, "Reset token save हुन सकेन"
    return token, "Token सिर्जना भयो"


def verify_reset_token(token):
    """Token valid छ कि जाँच्ने."""
    tokens = _load_tokens()
    if token not in tokens:
        return False, "Token गलत छ"

    data = tokens[token]
    if data.get("used"):
        return False, "Token पहिले नै प्रयोग भइसक्यो"

    try:
        if datetime.now() > datetime.fromisoformat(data["expiry"]):
            return False, "Token expired (१ घण्टा पछि)"
    except (ValueError, KeyError, TypeError):
        return False, "Token गलत"

    return True, data["username"]


def consume_reset_token(token, new_password):
    """Token प्रयोग गरेर password reset."""
    valid, result = verify_reset_token(token)
    if not valid:
        return False, result

    username = result
    new_password = str(new_password or "")
    if len(new_password) < 6:
        return False, "Password कम्तिमा ६ अक्षर"

    users = _load_users()
    if username not in users:
        return False, "User भेटिएन"

    users[username]["password"] = bcrypt.hashpw(
        new_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    users[username]["failed_attempts"] = 0
    users[username]["locked_until"] = None

    if not _save_users(users):
        return False, "Password save हुन सकेन"

    tokens = _load_tokens()
    if token in tokens:
        tokens[token]["used"] = True
        tokens[token]["used_at"] = datetime.now().isoformat()
        if not _save_tokens(tokens):
            return False, "Reset token update हुन सकेन"

    return True, f"Password reset भयो ({username})"


# ============================================================
# OTP-BASED RESET (6-digit code)
# ============================================================
def _load_otps():
    return _load_json(OTP_FILE)


def _save_otps(otps):
    return _save_json(OTP_FILE, otps)


def generate_otp(username, email=None):
    """६-अंकको OTP (५ मिनेट valid)."""
    users = _load_users()
    if username not in users:
        return None, "User भेटिएन"

    user_email = str(email or users[username].get("email", "")).strip()
    if not user_email:
        return None, "User को email छैन"
    if user_email.lower() != str(users[username].get("email", "")).lower():
        return None, "Account email मिलेन"

    otp_code = f"{secrets.randbelow(900000) + 100000}"
    expiry = (datetime.now() + timedelta(minutes=5)).isoformat()

    otps = _load_otps()
    otps = {k: v for k, v in otps.items() if v.get("username") != username}
    otps[username] = {
        "otp": otp_code,
        "email": user_email,
        "expiry": expiry,
        "attempts": 0,
        "used": False
    }
    if not _save_otps(otps):
        return None, "OTP save हुन सकेन"
    return otp_code, "OTP सिर्जना भयो"


def verify_otp(username, otp_code):
    """OTP valid छ कि जाँच्ने."""
    otps = _load_otps()
    if username not in otps:
        return False, "OTP भेटिएन। फेरि अनुरोध गर्नुहोस्।"

    data = otps[username]
    if data.get("used"):
        return False, "OTP पहिले नै प्रयोग भइसक्यो"

    try:
        if datetime.now() > datetime.fromisoformat(data["expiry"]):
            return False, "OTP expired (५ मिनेट पछि)"
    except (ValueError, KeyError, TypeError):
        return False, "OTP गलत"

    if data.get("attempts", 0) >= 3:
        return False, "धेरै पटक गलत। नयाँ OTP अनुरोध गर्नुहोस्।"

    if not secrets.compare_digest(str(otp_code).strip(), str(data.get("otp", ""))):
        otps[username]["attempts"] = data.get("attempts", 0) + 1
        _save_otps(otps)
        remaining = 3 - otps[username]["attempts"]
        return False, f"गलत OTP। {remaining} प्रयास बाँकी।"

    return True, username


def reset_password_with_otp(username, otp_code, new_password):
    """OTP verify गरेर password reset."""
    valid, result = verify_otp(username, otp_code)
    if not valid:
        return False, result

    new_password = str(new_password or "")
    if len(new_password) < 6:
        return False, "Password कम्तिमा ६ अक्षर"

    users = _load_users()
    if username not in users:
        return False, "User भेटिएन"

    users[username]["password"] = bcrypt.hashpw(
        new_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    users[username]["failed_attempts"] = 0
    users[username]["locked_until"] = None

    if not _save_users(users):
        return False, "Password save हुन सकेन"

    otps = _load_otps()
    if username in otps:
        otps[username]["used"] = True
        otps[username]["used_at"] = datetime.now().isoformat()
        if not _save_otps(otps):
            return False, "OTP status save हुन सकेन"

    return True, f"Password reset भयो ({username})"


# ============================================================
# BASIC SELF-TEST
# ============================================================
if __name__ == "__main__":
    print("auth.py syntax/import self-test")
    print("Language normalizer (ne):", _normalize_language("ne"))
    print("Language normalizer (en-US):", _normalize_language("en-US"))
    print("Language normalizer (zh-CN):", _normalize_language("zh-CN"))
    print("Language normalizer (invalid):", _normalize_language("xx"))
    print("Supported languages:", len(get_supported_languages()))
    print("is_language_supported('hi'):", is_language_supported("hi"))
    print("Password strength helper:", check_password_strength("Test123!"))
    print("Email validator:", validate_email("test@example.com"))
    print("Username validator:", validate_username("testuser"))
    print("user_exists_by_email('test@example.com'):", user_exists_by_email("test@example.com"))
    print("Auth module self-test completed.")