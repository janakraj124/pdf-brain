# email_helper.py — PDF Brain (Multi-Language + Audit)
import os
import time
import logging
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

from translations import TRANSLATIONS
from audit_logger import log_event

load_dotenv()

logging.basicConfig(
    filename="email_errors.log",
    level=logging.ERROR,
    format="%(asctime)s — %(levelname)s — %(message)s"
)


# ============================================================
# SMTP Config (Multi-provider)
# ============================================================
def _get_smtp_config():
    provider = os.getenv("EMAIL_PROVIDER", "gmail").lower()
    configs = {
        "gmail":    {"host": "smtp.gmail.com",    "port": 587},
        "sendgrid": {"host": "smtp.sendgrid.net","port": 587},
        "mailgun":  {"host": "smtp.mailgun.org", "port": 587},
        "ses":      {"host": "email-smtp.us-east-1.amazonaws.com", "port": 587},
    }
    cfg = configs.get(provider, configs["gmail"])
    return {
        "host": cfg["host"],
        "port": cfg["port"],
        "user": os.getenv("SMTP_USER", ""),
        "pass": os.getenv("SMTP_PASS", ""),
        "from_name": os.getenv("FROM_NAME", "PDF Brain"),
    }


def _send_with_retry(msg, max_retries=2):
    """SMTP पठाउने — retry सहित"""
    cfg = _get_smtp_config()
    if not cfg["user"] or not cfg["pass"]:
        return False, "SMTP config .env मा छैन"

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=15) as server:
                server.starttls()
                server.login(cfg["user"], cfg["pass"])
                server.send_message(msg)
            return True, None
        except smtplib.SMTPAuthenticationError as e:
            logging.error(f"Auth failed: {e}")
            return False, f"Authentication failed: {e}"
        except Exception as e:
            last_error = e
            logging.error(f"SMTP attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)
    return False, str(last_error)


# ============================================================
# Templates (Multi-language)
# ============================================================
def _get_otp_template(lang="ne", purpose="signup"):
    T = TRANSLATIONS.get(lang, TRANSLATIONS.get("en", {}))
    if purpose == "signup":
        title = T.get("otp_email_signup_title", "Account Verification Code")
        intro = T.get("otp_email_signup_intro", "Use this code to verify your account:")
    else:
        title = T.get("otp_email_reset_title", "Password Reset Code")
        intro = T.get("otp_email_reset_intro", "Use this code to reset your password:")

    expiry = T.get("otp_email_expiry", "This code is valid for 5 minutes.")
    ignore = T.get("otp_email_ignore", "If you did not request this, ignore this email.")
    footer = T.get("footer", "Made with ❤️ in Nepal")

    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto;
                border: 1px solid #e0e0e0; border-radius: 12px; overflow: hidden;">
        <div style="background: linear-gradient(90deg, #667eea, #764ba2);
                    padding: 20px; text-align: center; color: white;">
            <h2 style="margin: 0;">🧠 PDF Brain</h2>
        </div>
        <div style="padding: 30px; text-align: center;">
            <h3 style="color: #333;">{title}</h3>
            <p style="color: #666;">{intro}</p>
            <div style="font-size: 36px; font-weight: bold; letter-spacing: 8px;
                        color: #667eea; padding: 15px; background: #f0f3ff;
                        border-radius: 10px; margin: 20px 0;">
                {{otp}}
            </div>
            <p style="color: #999; font-size: 12px;">{expiry}</p>
            <p style="color: #999; font-size: 12px;">{ignore}</p>
        </div>
        <div style="background: #f8f9fa; padding: 15px; text-align: center;
                    color: #999; font-size: 12px;">
            {footer} — PDF Brain
        </div>
    </div>
    """


def _get_reset_template(lang="ne"):
    T = TRANSLATIONS.get(lang, TRANSLATIONS.get("en", {}))
    title = T.get("reset_email_title", "Password Reset")
    intro = T.get("reset_email_intro", "Click the button below to reset your password:")
    btn = T.get("reset_email_btn", "Reset Password")
    expiry = T.get("reset_email_expiry", "This link is valid for 1 hour.")
    footer = T.get("footer", "Made with ❤️ in Nepal")

    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #667eea;">🔑 {title}</h2>
        <p>{intro}</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{{reset_link}}" style="background: linear-gradient(135deg, #667eea, #764ba2);
               color: white; padding: 12px 30px; text-decoration: none;
               border-radius: 8px; font-weight: bold;">{btn}</a>
        </p>
        <p style="color: #666; font-size: 0.9em;">⚠️ {expiry}</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 0.8em;">🧠 PDF Brain · {footer}</p>
    </div>
    """


# ============================================================
# Public functions
# ============================================================
def send_otp_email(to_email, otp_code, username="", lang="ne", purpose="signup"):
    """OTP email — multi-language + audit + retry"""
    try:
        cfg = _get_smtp_config()
        if not cfg["user"] or not cfg["pass"]:
            log_event("email_sent", email=to_email, purpose=purpose,
                      action="otp", status="fail",
                      details={"reason": "no_smtp_config"})
            return {"success": False, "error": "SMTP config .env मा छैन"}

        # Subject (multi-language)
        T = TRANSLATIONS.get(lang, TRANSLATIONS.get("en", {}))
        if purpose == "signup":
            subject = T.get("otp_email_signup_subject", "PDF Brain — Verification Code")
        else:
            subject = T.get("otp_email_reset_subject", "PDF Brain — Password Reset Code")

        msg = EmailMessage()
        msg["From"] = f"{cfg['from_name']} <{cfg['user']}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        # Plain text
        msg.set_content(
            f"Your OTP code: {otp_code}\n\n"
            f"Valid for 5 minutes.\n\n"
            f"If you did not request this, ignore this email."
        )

        # HTML (multi-language)
        html = _get_otp_template(lang, purpose).replace("{otp}", otp_code)
        msg.add_alternative(html, subtype="html")

        ok, err = _send_with_retry(msg)

        if ok:
            log_event("email_sent", email=to_email, purpose=purpose,
                      action="otp", status="success")
            return {"success": True}
        else:
            log_event("email_sent", email=to_email, purpose=purpose,
                      action="otp", status="fail", details={"error": err})
            return {"success": False, "error": err}

    except Exception as e:
        log_event("email_sent", email=to_email, purpose=purpose,
                  action="otp", status="error", details={"error": str(e)})
        return {"success": False, "error": str(e)}


def send_reset_email(to_email, reset_link, username="", lang="ne"):
    """Reset link email — multi-language + audit"""
    try:
        cfg = _get_smtp_config()
        if not cfg["user"] or not cfg["pass"]:
            log_event("email_sent", email=to_email, purpose="reset",
                      action="reset_link", status="fail",
                      details={"reason": "no_smtp_config"})
            return {"success": False, "error": "SMTP config .env मा छैन"}

        T = TRANSLATIONS.get(lang, TRANSLATIONS.get("en", {}))
        subject = T.get("reset_email_subject", "PDF Brain — Password Reset")

        msg = EmailMessage()
        msg["From"] = f"{cfg['from_name']} <{cfg['user']}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.set_content(
            f"Password reset link: {reset_link}\n\n"
            f"Valid for 1 hour.\n\n"
            f"If you did not request this, ignore this email."
        )

        html = _get_reset_template(lang).replace("{reset_link}", reset_link)
        msg.add_alternative(html, subtype="html")

        ok, err = _send_with_retry(msg)

        if ok:
            log_event("email_sent", email=to_email, purpose="reset",
                      action="reset_link", status="success")
            return {"success": True}
        else:
            log_event("email_sent", email=to_email, purpose="reset",
                      action="reset_link", status="fail", details={"error": err})
            return {"success": False, "error": err}

    except Exception as e:
        log_event("email_sent", email=to_email, purpose="reset",
                  action="reset_link", status="error", details={"error": str(e)})
        return {"success": False, "error": str(e)}


def send_email(to_email, subject, body, username="", lang="ne"):
    """सामान्य email — audit सहित"""
    try:
        cfg = _get_smtp_config()
        if not cfg["user"] or not cfg["pass"]:
            return {"success": False, "error": "SMTP config .env मा छैन"}

        msg = EmailMessage()
        msg["From"] = f"{cfg['from_name']} <{cfg['user']}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.set_content(body)

        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #667eea;">{subject}</h2>
            <p>नमस्ते {username or "प्रयोगकर्ता"},</p>
            <div style="line-height: 1.7;">{body.replace(chr(10), "<br>")}</div>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 0.8em;">🧠 PDF Brain</p>
        </div>
        """
        msg.add_alternative(html, subtype="html")

        ok, err = _send_with_retry(msg)

        if ok:
            log_event("email_sent", email=to_email, action="general",
                      status="success")
            return {"success": True}
        else:
            log_event("email_sent", email=to_email, action="general",
                      status="fail", details={"error": err})
            return {"success": False, "error": err}

    except Exception as e:
        log_event("email_sent", email=to_email, action="general",
                  status="error", details={"error": str(e)})
        return {"success": False, "error": str(e)}