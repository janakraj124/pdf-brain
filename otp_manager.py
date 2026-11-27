# otp_manager.py — PDF Brain (Audit + Secure OTP)
import os
import json
import secrets
import hashlib
from datetime import datetime, timedelta

from audit_logger import log_event

OTP_DIR = "otp_data"
os.makedirs(OTP_DIR, exist_ok=True)

OTP_EXPIRY_MINUTES = 5
MAX_ATTEMPTS = 3
RATE_LIMIT_WINDOW = 60
MAX_REQUESTS_PER_WINDOW = 3


def _otp_file(email):
    safe = hashlib.md5(email.lower().strip().encode()).hexdigest()
    return os.path.join(OTP_DIR, f"{safe}.json")


def can_request_otp(email):
    """Rate limit check"""
    path = _otp_file(email)
    if not os.path.exists(path):
        return True, "OK"

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        last = datetime.fromisoformat(data.get("created_at", "2000-01-01"))
        elapsed = (datetime.now() - last).total_seconds()
        if elapsed < RATE_LIMIT_WINDOW:
            remaining = int(RATE_LIMIT_WINDOW - elapsed)
            return False, f"कृपया {remaining} सेकेन्ड पर्खनुहोस्।"
        return True, "OK"
    except Exception:
        return True, "OK"


def generate_otp(email, purpose="signup"):
    """Secure OTP generate + hash save + audit"""
    email = email.lower().strip()

    # Cryptographically secure OTP
    otp = str(secrets.randbelow(900000) + 100000)
    otp_hash = hashlib.sha256(otp.encode()).hexdigest()

    data = {
        "email": email,
        "otp_hash": otp_hash,
        "purpose": purpose,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat(),
        "attempts": 0,
        "verified": False,
    }
    with open(_otp_file(email), "w", encoding="utf-8") as f:
        json.dump(data, f)

    # Audit
    log_event(
        event_type="otp_request",
        email=email,
        purpose=purpose,
        action="generate",
        status="success"
    )

    return otp


def verify_otp(email, entered_otp):
    """OTP verify + audit"""
    email = email.lower().strip()
    path = _otp_file(email)

    if not os.path.exists(path):
        log_event("otp_verify", email=email, action="verify",
                  status="fail", details={"reason": "no_otp"})
        return False, "OTP फेला परेन। कृपया पुनः पठाउनुहोस्।"

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return False, "OTP file पढ्न सकिएन।"

    # Expiry
    if datetime.now() > datetime.fromisoformat(data["expires_at"]):
        os.remove(path)
        log_event("otp_verify", email=email, action="verify",
                  status="fail", details={"reason": "expired"})
        return False, "OTP को समय सकियो। कृपया पुनः पठाउनुहोस्।"

    # Attempts
    if data["attempts"] >= MAX_ATTEMPTS:
        os.remove(path)
        log_event("otp_verify", email=email, action="verify",
                  status="blocked", details={"reason": "max_attempts"})
        return False, "धेरै पटक गलत OTP। कृपया पुनः पठाउनुहोस्।"

    # Check hash
    entered_hash = hashlib.sha256(entered_otp.strip().encode()).hexdigest()
    if entered_hash != data["otp_hash"]:
        data["attempts"] += 1
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        remaining = MAX_ATTEMPTS - data["attempts"]
        log_event("otp_verify", email=email, action="verify",
                  status="fail", details={"reason": "wrong_otp", "attempts": data["attempts"]})
        return False, f"गलत OTP। {remaining} प्रयास बाँकी।"

    # Success
    data["verified"] = True
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    log_event("otp_verify", email=email, action="verify",
              status="success")
    return True, "OTP सफल भयो।"


def is_verified(email):
    path = _otp_file(email)
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("verified", False)
    except Exception:
        return False


def clear_otp(email):
    path = _otp_file(email)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False