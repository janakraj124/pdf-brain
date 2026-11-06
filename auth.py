# auth.py — PDF Brain (Powerful Auth System v3 — Token + OTP)
import os
import json
import bcrypt
import re
import random
import secrets
from datetime import datetime, timedelta

USERS_FILE = "users.json"
RESET_TOKEN_FILE = "reset_tokens.json"
OTP_FILE = "reset_otp.json"


# ============================================================
# 📁 FILE HELPERS
# ============================================================
def _load_users():
    """Users file पढ्ने (वा bootstrap admin बनाउने)"""
    if not os.path.exists(USERS_FILE):
        # ✅ Bootstrap: Streamlit Secrets बाट admin बनाउने
        try:
            import streamlit as st
            bootstrap_user = st.secrets.get("BOOTSTRAP_ADMIN_USERNAME", "")
            bootstrap_pass = st.secrets.get("BOOTSTRAP_ADMIN_PASSWORD", "")
            bootstrap_email = st.secrets.get("BOOTSTRAP_ADMIN_EMAIL", "")

            if bootstrap_user and bootstrap_pass:
                print(f"🔐 Bootstrap admin बन्दैछ: {bootstrap_user}")
                default = {
                    bootstrap_user: {
                        "password": bcrypt.hashpw(bootstrap_pass.encode(), bcrypt.gensalt()).decode(),
                        "role": "admin",
                        "email": bootstrap_email,
                        "created": datetime.now().isoformat(),
                        "last_login": None,
                        "login_count": 0,
                        "failed_attempts": 0,
                        "locked_until": None,
                        "profile": {"name": "Admin", "phone": ""}
                    }
                }
                _save_users(default)
                return default
        except Exception as e:
            print(f"[BOOTSTRAP WARNING] {e}")

        # ⚠️ Fallback: यदि secrets छैन भने default admin
        # (Deploy अघि create_admin.py चलाउनुहोस् — यो fallback पछि हटाउनुहोस्)
        print("⚠️ BOOTSTRAP secrets भेटिएन — fallback default admin बन्दैछ")
        default = {
            "admin": {
                "password": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
                "role": "admin",
                "email": "admin@pdfbrain.com",
                "created": datetime.now().isoformat(),
                "last_login": None,
                "login_count": 0,
                "failed_attempts": 0,
                "locked_until": None,
                "profile": {"name": "Admin", "phone": ""}
            }
        }
        _save_users(default)
        return default

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[LOAD ERROR] {e}")
        return {}


def _save_users(users):
    """Users file save गर्ने"""
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[SAVE ERROR] {e}")
        return False


def _load_json(filepath):
    """Generic JSON load"""
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def _save_json(filepath, data):
    """Generic JSON save"""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"[SAVE ERROR] {e}")
        return False


# ============================================================
# 🔍 VALIDATION
# ============================================================
def validate_email(email):
    """Email format जाँच"""
    if not email:
        return True
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))


def validate_username(username):
    """Username format जाँच"""
    if len(username) < 3:
        return False, "Username कम्तिमा ३ अक्षर"
    if len(username) > 20:
        return False, "Username अधिकतम २० अक्षर"
    if not re.match(r'^[\w]+$', username):
        return False, "Username: अक्षर, अंक, _ मात्र"
    return True, "OK"


def check_password_strength(password):
    """Password strength (0-5)"""
    score = 0
    if len(password) >= 8: score += 1
    if any(c.isupper() for c in password): score += 1
    if any(c.islower() for c in password): score += 1
    if any(c.isdigit() for c in password): score += 1
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password): score += 1
    return score


# ============================================================
# 👤 USER MANAGEMENT
# ============================================================
def create_user(username, password, email="", role="user"):
    """नयाँ user बनाउने"""
    users = _load_users()

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
        for u, data in users.items():
            if data.get("email") == email:
                return False, "Email पहिले नै प्रयोग भएको छ"

    users[username] = {
        "password": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
        "role": role,
        "email": email,
        "created": datetime.now().isoformat(),
        "last_login": None,
        "login_count": 0,
        "failed_attempts": 0,
        "locked_until": None,
        "profile": {"name": username, "phone": ""}
    }
    _save_users(users)
    return True, "User सफलतापूर्वक बन्यो"


def verify_user(username, password):
    """Login verify गर्ने"""
    users = _load_users()

    if username not in users:
        for u, data in users.items():
            if data.get("email", "").lower() == username.lower():
                username = u   # email → actual username
                break
        else:
            return False, {}

    user = users[username]

    locked_until = user.get("locked_until")
    if locked_until:
        try:
            if datetime.now() < datetime.fromisoformat(locked_until):
                return False, {"locked": True, "until": locked_until}
            else:
                users[username]["locked_until"] = None
                users[username]["failed_attempts"] = 0
                _save_users(users)
        except:
            pass

    try:
        if bcrypt.checkpw(password.encode(), user["password"].encode()):
            users[username]["last_login"] = datetime.now().isoformat()
            users[username]["login_count"] = user.get("login_count", 0) + 1
            users[username]["failed_attempts"] = 0
            _save_users(users)

            return True, {
                "username": username,
                "role": user.get("role", "user"),
                "email": user.get("email", ""),
                "profile": user.get("profile", {}),
                "last_login": users[username]["last_login"],
                "login_count": users[username]["login_count"]
            }
        else:
            users[username]["failed_attempts"] = user.get("failed_attempts", 0) + 1
            if users[username]["failed_attempts"] >= 5:
                users[username]["locked_until"] = (
                    datetime.now() + timedelta(minutes=5)
                ).isoformat()
            _save_users(users)
            return False, {"failed": True, "attempts": users[username]["failed_attempts"]}
    except Exception as e:
        print(f"[AUTH ERROR] {e}")

    return False, {}


def update_user_profile(username, name="", email="", phone=""):
    """User profile update"""
    users = _load_users()
    if username not in users:
        return False, "User छैन"

    if email and not validate_email(email):
        return False, "Email format गलत"

    if email:
        users[username]["email"] = email
    if name:
        if "profile" not in users[username]:
            users[username]["profile"] = {}
        users[username]["profile"]["name"] = name
    if phone:
        if "profile" not in users[username]:
            users[username]["profile"] = {}
        users[username]["profile"]["phone"] = phone

    _save_users(users)
    return True, "Profile update भयो"


def change_password(username, old_password, new_password):
    """Password फेर्ने (old verify सहित)"""
    users = _load_users()
    if username not in users:
        return False, "User छैन"

    try:
        if not bcrypt.checkpw(old_password.encode(), users[username]["password"].encode()):
            return False, "पुरानो password गलत"
    except Exception as e:
        return False, f"Error: {e}"

    if len(new_password) < 6:
        return False, "नयाँ password कम्तिमा ६ अक्षर"

    users[username]["password"] = bcrypt.hashpw(
        new_password.encode(), bcrypt.gensalt()
    ).decode()
    _save_users(users)
    return True, "Password फेरियो"


def reset_password(username, new_password):
    """Admin द्वारा password reset"""
    users = _load_users()
    if username not in users:
        return False, "User छैन"

    if len(new_password) < 6:
        return False, "Password कम्तिमा ६ अक्षर"

    users[username]["password"] = bcrypt.hashpw(
        new_password.encode(), bcrypt.gensalt()
    ).decode()
    users[username]["failed_attempts"] = 0
    users[username]["locked_until"] = None
    _save_users(users)
    return True, "Password reset भयो"


def update_user_role(username, new_role):
    """Admin द्वारा role change"""
    users = _load_users()
    if username not in users:
        return False, "User छैन"
    if new_role not in ["user", "manager", "admin"]:
        return False, "Invalid role"
    users[username]["role"] = new_role
    _save_users(users)
    return True, f"Role → {new_role}"


# ============================================================
# 📋 LIST & STATS
# ============================================================
def list_users():
    """सबै users list (stats सहित)"""
    users = _load_users()
    result = []
    for u, data in users.items():
        result.append({
            "username": u,
            "role": data.get("role", "user"),
            "email": data.get("email", ""),
            "created": data.get("created", ""),
            "last_login": data.get("last_login", ""),
            "login_count": data.get("login_count", 0),
            "failed_attempts": data.get("failed_attempts", 0),
            "locked": bool(data.get("locked_until"))
        })
    return result


def get_user_info(username):
    """एक user को पूरा info"""
    users = _load_users()
    if username not in users:
        return None
    data = users[username].copy()
    data.pop("password", None)
    data["username"] = username
    return data


def delete_user(username):
    """User हटाउने (admin बाहेक)"""
    users = _load_users()
    if username in users and username != "admin":
        del users[username]
        _save_users(users)
        return True
    return False


def unlock_user(username):
    """Locked user unlock"""
    users = _load_users()
    if username in users:
        users[username]["locked_until"] = None
        users[username]["failed_attempts"] = 0
        _save_users(users)
        return True
    return False


# ============================================================
# 🔗 TOKEN-BASED RESET (Link)
# ============================================================
def _load_tokens():
    return _load_json(RESET_TOKEN_FILE)


def _save_tokens(tokens):
    return _save_json(RESET_TOKEN_FILE, tokens)


def generate_reset_token(username, email=None):
    """Reset token बनाउने (१ घण्टा valid)"""
    users = _load_users()

    if username not in users:
        return None, "User भेटिएन"

    user_email = email or users[username].get("email", "")
    if not user_email:
        return None, "User को email छैन"

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
    _save_tokens(tokens)

    return token, "Token सिर्जना भयो"


def find_user_by_email(email):
    """Email बाट username खोज्ने"""
    users = _load_users()
    for username, data in users.items():
        if data.get("email", "").lower() == email.lower():
            return username
    return None


def verify_reset_token(token):
    """Token valid छ कि जाँच्ने"""
    tokens = _load_tokens()

    if token not in tokens:
        return False, "Token गलत छ"

    data = tokens[token]

    if data.get("used"):
        return False, "Token पहिले नै प्रयोग भइसक्यो"

    try:
        if datetime.now() > datetime.fromisoformat(data["expiry"]):
            return False, "Token expired (१ घण्टा पछि)"
    except:
        return False, "Token गलत"

    return True, data["username"]


def consume_reset_token(token, new_password):
    """Token प्रयोग गरेर password reset"""
    valid, result = verify_reset_token(token)

    if not valid:
        return False, result

    username = result

    if len(new_password) < 6:
        return False, "Password कम्तिमा ६ अक्षर"

    users = _load_users()
    if username not in users:
        return False, "User भेटिएन"

    users[username]["password"] = bcrypt.hashpw(
        new_password.encode(), bcrypt.gensalt()
    ).decode()
    users[username]["failed_attempts"] = 0
    users[username]["locked_until"] = None
    _save_users(users)

    tokens = _load_tokens()
    if token in tokens:
        tokens[token]["used"] = True
        tokens[token]["used_at"] = datetime.now().isoformat()
        _save_tokens(tokens)

    return True, f"Password reset भयो ({username})"


# ============================================================
# 🔢 OTP-BASED RESET (६-अंक Code)
# ============================================================
def _load_otps():
    return _load_json(OTP_FILE)


def _save_otps(otps):
    return _save_json(OTP_FILE, otps)


def generate_otp(username, email=None):
    """६-अंकको OTP बनाउने (५ मिनेट valid)"""
    users = _load_users()

    if username not in users:
        return None, "User भेटिएन"

    user_email = email or users[username].get("email", "")
    if not user_email:
        return None, "User को email छैन"

    otp_code = str(random.randint(100000, 999999))
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
    _save_otps(otps)

    return otp_code, "OTP सिर्जना भयो"


def verify_otp(username, otp_code):
    """OTP valid छ कि जाँच्ने"""
    otps = _load_otps()

    if username not in otps:
        return False, "OTP भेटिएन। फेरि अनुरोध गर्नुहोस्।"

    data = otps[username]

    if data.get("used"):
        return False, "OTP पहिले नै प्रयोग भइसक्यो"

    try:
        if datetime.now() > datetime.fromisoformat(data["expiry"]):
            return False, "OTP expired (५ मिनेट पछि)"
    except:
        return False, "OTP गलत"

    if data.get("attempts", 0) >= 3:
        return False, "धेरै पटक गलत। नयाँ OTP अनुरोध गर्नुहोस्।"

    if str(otp_code).strip() != data["otp"]:
        otps[username]["attempts"] = data.get("attempts", 0) + 1
        _save_otps(otps)
        remaining = 3 - otps[username]["attempts"]
        return False, f"गलत OTP। {remaining} प्रयास बाँकी।"

    return True, username


def reset_password_with_otp(username, otp_code, new_password):
    """OTP verify गरेर password reset"""
    valid, result = verify_otp(username, otp_code)

    if not valid:
        return False, result

    if len(new_password) < 6:
        return False, "Password कम्तिमा ६ अक्षर"

    users = _load_users()
    if username not in users:
        return False, "User भेटिएन"

    users[username]["password"] = bcrypt.hashpw(
        new_password.encode(), bcrypt.gensalt()
    ).decode()
    users[username]["failed_attempts"] = 0
    users[username]["locked_until"] = None
    _save_users(users)

    otps = _load_otps()
    if username in otps:
        otps[username]["used"] = True
        otps[username]["used_at"] = datetime.now().isoformat()
        _save_otps(otps)

    return True, f"Password reset भयो ({username})"


# ============================================================
# 🧪 TEST
# ============================================================
if __name__ == "__main__":
    print("🧪 Testing auth.py...\n")

    ok, user = verify_user("admin", "admin123")
    print(f"Admin login: {'✅' if ok else '❌'} — role: {user.get('role') if ok else 'N/A'}")

    ok, msg = create_user("testuser", "test123456", "test@example.com")
    print(f"Create user: {'✅' if ok else '❌'} — {msg}")

    ok, user = verify_user("testuser", "test123456")
    print(f"Test login: {'✅' if ok else '❌'} — role: {user.get('role') if ok else 'N/A'}")

    print(f"\n📋 Users:")
    for u in list_users():
        print(f"   • {u['username']} ({u['role']}) — last login: {u['last_login'][:10] if u['last_login'] else 'never'}")