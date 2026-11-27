# email_server.py — PDF Brain v54.0 (AI Spam Filter + Audit + Retry)
import os
import re
import ssl
import time
import email
import signal
import smtplib
import imaplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, formataddr
from datetime import datetime
from dotenv import load_dotenv

from answer import answer_question
from audit_logger import log_event
from spam_filter import is_spam as ai_is_spam

load_dotenv()

# ============================================================
# Configuration
# ============================================================
EMAIL = os.getenv("EMAIL", "")
PASSWORD = os.getenv("EMAIL_PASSWORD", "").replace(" ", "")
EMAIL_CHECK_INTERVAL = int(os.getenv("EMAIL_CHECK_INTERVAL", "60"))

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
IMAP_HOST = "imap.gmail.com"

# Email processing limits
MAX_EMAILS_PER_CHECK = 10       # बढाइयो (पहिले 5)
MAX_BODY_LENGTH = 1500
MIN_BODY_LENGTH = 5
MARK_AS_READ = True

# AI Spam filter enable/disable
USE_AI_SPAM_FILTER = os.getenv("USE_AI_SPAM_FILTER", "true").lower() == "true"


# ============================================================
# Logging setup
# ============================================================
logging.basicConfig(
    filename="email_server_errors.log",
    level=logging.ERROR,
    format="%(asctime)s — %(levelname)s — %(message)s"
)


# ============================================================
# Colors for Terminal Output
# ============================================================
class C:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def log_header(msg):
    print(f"\n{C.BOLD}{C.CYAN}{'='*60}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{msg}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{'='*60}{C.END}\n")


def log_success(msg):
    print(f"{C.GREEN}✅ {msg}{C.END}")


def log_error(msg):
    print(f"{C.RED}❌ {msg}{C.END}")


def log_warning(msg):
    print(f"{C.YELLOW}⚠️  {msg}{C.END}")


def log_info(msg):
    print(f"{C.BLUE}ℹ️  {msg}{C.END}")


def log_skip(msg):
    print(f"{C.YELLOW}⏭️  {msg}{C.END}")


# ============================================================
# Send Email (Retry + Logging सहित)
# ============================================================
def send_email(to, subject, body, html_body=None, max_retries=2):
    """Email पठाउने — HTML + Plain text + retry"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"PDF Brain <{EMAIL}>"
        msg["To"] = to

        # Plain text
        text_part = MIMEText(body, "plain", "utf-8")
        msg.attach(text_part)

        # HTML version
        if html_body is None:
            body_html = body.replace("\n", "<br>")
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', system-ui, sans-serif;
                        line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .header {{ background: linear-gradient(135deg, #667eea, #764ba2);
                           color: white; padding: 25px; border-radius: 12px 12px 0 0;
                           text-align: center; }}
                .header h2 {{ margin: 0; font-size: 1.8em; }}
                .content {{ background: #ffffff; padding: 30px;
                            border-left: 1px solid #eee; border-right: 1px solid #eee; }}
                .footer {{ background: #f8f9fa; padding: 20px;
                           border-radius: 0 0 12px 12px; text-align: center;
                           color: #666; font-size: 0.9em;
                           border: 1px solid #eee; }}
            </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>🧠 PDF Brain</h2>
                        <small>AI-powered PDF Assistant</small>
                    </div>
                    <div class="content">{body_html}</div>
                    <div class="footer">
                        📧 Automatic reply from PDF Brain<br>
                        ⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}<br>
                        <small style="opacity: 0.7;">
                            यो email automatic हो। Reply गर्नु आवश्यक छैन।
                        </small>
                    </div>
                </div>
            </body>
            </html>
            """

        html_part = MIMEText(html_body, "html", "utf-8")
        msg.attach(html_part)

        # Retry logic
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                # Port अनुसार SSL/TLS
                if SMTP_PORT == 465:
                    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as server:
                        server.login(EMAIL, PASSWORD)
                        server.send_message(msg)
                else:
                    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
                        server.starttls()
                        server.login(EMAIL, PASSWORD)
                        server.send_message(msg)

                log_success(f"Email पठाइयो: {to}")
                return True

            except smtplib.SMTPAuthenticationError as e:
                logging.error(f"SMTP auth failed: {e}")
                log_error(f"SMTP Authentication failed — .env जाँच्नुहोस्")
                return False

            except Exception as e:
                last_error = e
                logging.error(f"SMTP attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)

        log_error(f"Email send error (after retries): {last_error}")
        return False

    except Exception as e:
        logging.error(f"Email compose error: {e}")
        log_error(f"Email send error: {e}")
        return False


# ============================================================
# Extract Email Body (सफा)
# ============================================================
def get_email_body(msg):
    """Email बाट सफा text निकाल्ने (HTML + quote सफा)"""
    body = ""

    if msg.is_multipart():
        # पहिले text/plain
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    if body.strip():
                        break
                except Exception:
                    pass

        # text/plain भेटिएन भने text/html
        if not body.strip():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                if content_type == "text/html" and "attachment" not in content_disposition:
                    try:
                        html = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        body = _clean_html(html)
                        if body.strip():
                            break
                    except Exception:
                        pass
    else:
        try:
            raw = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            if "<html" in raw.lower() or "<body" in raw.lower() or "<div" in raw.lower():
                body = _clean_html(raw)
            else:
                body = raw
        except Exception:
            pass

    body = _remove_quotes(body)
    body = re.sub(r'\s+', ' ', body).strip()
    return body


def _clean_html(html):
    """HTML बाट text मात्र निकाल्ने"""
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<head[^>]*>.*?</head>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</p>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</div>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'<[^>]+>', ' ', html)

    entities = {
        '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>',
        '&quot;': '"', '&#39;': "'", '&apos;': "'",
        '&copy;': '©', '&reg;': '®', '&trade;': '™',
        '&hellip;': '...', '&mdash;': '—', '&ndash;': '–'
    }
    for entity, char in entities.items():
        html = html.replace(entity, char)

    html = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))) if int(m.group(1)) < 1114111 else '', html)
    return html.strip()


def _remove_quotes(body):
    """पुरानो email thread हटाउने"""
    patterns = [
        r'On .{5,100} wrote:',
        r'-----Original Message-----',
        r'From: .{5,100}\n',
        r'_{10,}',
        r'---+\s*Forwarded message',
        r'On \d{1,2}/\d{1,2}/\d{2,4}',
        r'Sent from my ',
        r'Get Outlook for ',
        r'________________________________'
    ]
    for pattern in patterns:
        if re.search(pattern, body):
            body = re.split(pattern, body)[0]
    return body.strip()


# ============================================================
# Extract Sender + Attachments
# ============================================================
def _extract_sender(msg):
    """Sender email निकाल्ने (safe parseaddr)"""
    raw = msg.get("From", "")
    name, addr = parseaddr(raw)
    return addr.strip().lower(), name.strip()


def _has_attachments(msg):
    """Attachment छ कि जाँच्ने — (bool, list)"""
    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            cd = str(part.get("Content-Disposition", ""))
            if "attachment" in cd:
                fname = part.get_filename() or "unknown"
                attachments.append(fname)
    return bool(attachments), attachments


def _build_reply_subject(subject):
    """Reply subject बनाउने — Re: duplicate नगर्ने"""
    if not subject:
        return "Re: (no subject)"
    s = subject.strip()
    if s.lower().startswith("re:"):
        return s
    return f"Re: {s}"


# ============================================================
# Spam Check Wrapper (AI + Rule)
# ============================================================
def is_spam(sender_email, subject, body_preview=""):
    """AI + Rule-based spam check wrapper"""
    try:
        spam, reason, confidence, method = ai_is_spam(
            sender_email, subject, body_preview, use_ai=USE_AI_SPAM_FILTER
        )
        return spam, reason
    except Exception as e:
        logging.error(f"Spam filter error: {e}")
        # AI fail भए rule-based fallback
        sender_lower = (sender_email or "").lower()
        subject_lower = (subject or "").lower()
        for kw in ["no-reply", "noreply", "newsletter", "marketing", "promo"]:
            if kw in sender_lower or kw in subject_lower:
                return True, f"fallback rule '{kw}'"
        return False, ""


# ============================================================
# Check Emails (Main logic)
# ============================================================
def check_new_emails():
    """नयाँ emails check गरेर auto-reply (message_handler सहित)"""
    from message_handler import handle_message

    stats = {
        "total": 0,
        "processed": 0,
        "skipped_spam": 0,
        "skipped_empty": 0,
        "skipped_self": 0,
        "errors": 0,
        "attachments": 0,
    }

    mail = None
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, timeout=30)
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            return stats

        email_ids = messages[0].split()
        stats["total"] = len(email_ids)

        if not email_ids:
            return stats

        log_info(f"📬 {len(email_ids)} UNSEEN emails भेटियो")
        email_ids = email_ids[-MAX_EMAILS_PER_CHECK:]
        log_info(f"🔍 अन्तिम {len(email_ids)} मात्र process...\n")

        for num in email_ids:
            try:
                status, msg_data = mail.fetch(num, "(RFC822)")
                if status != "OK":
                    continue

                msg = email.message_from_bytes(msg_data[0][1])

                # Sender parse
                sender_email, sender_name = _extract_sender(msg)

                # आफ्नै email skip
                if sender_email == EMAIL.lower():
                    stats["skipped_self"] += 1
                    mail.store(num, "+FLAGS", "\\Seen")
                    continue

                subject = msg["Subject"] or "(कुनै subject छैन)"

                # Body
                body = get_email_body(msg)[:MAX_BODY_LENGTH].strip()

                # Empty body skip
                if len(body) < MIN_BODY_LENGTH:
                    log_skip(f"Empty body: {sender_email}")
                    stats["skipped_empty"] += 1
                    mail.store(num, "+FLAGS", "\\Seen")
                    continue

                # Attachments
                has_att, att_list = _has_attachments(msg)
                if has_att:
                    stats["attachments"] += len(att_list)

                # Spam check (AI + Rule)
                spam, reason = is_spam(sender_email, subject, body[:200])
                if spam:
                    log_skip(f"Spam ({reason}): {sender_email}")
                    stats["skipped_spam"] += 1

                    # Audit log — spam blocked
                    log_event(
                        event_type="spam_blocked",
                        email=sender_email,
                        action="imap_filter",
                        status="blocked",
                        details={
                            "subject": subject[:200],
                            "reason": reason,
                            "has_attachments": has_att
                        }
                    )

                    mail.store(num, "+FLAGS", "\\Seen")
                    continue

                # Email details print
                print(f"{C.BOLD}📧 From:{C.END} {sender_email} ({sender_name})")
                print(f"{C.BOLD}   Subject:{C.END} {subject[:80]}")
                print(f"{C.BOLD}   Body:{C.END} {body[:120]}...")
                if has_att:
                    print(f"{C.BOLD}   Attachments:{C.END} {', '.join(att_list[:3])}")
                print()

                # User ID
                user_id = f"email_{sender_email}"

                # Message handler
                try:
                    reply = handle_message(user_id, body)
                except Exception as e:
                    logging.error(f"message_handler error: {e}")
                    log_error(f"Handler error: {e}")
                    stats["errors"] += 1
                    mail.store(num, "+FLAGS", "\\Seen")
                    continue

                if not reply:
                    log_skip("Empty response from handler")
                    mail.store(num, "+FLAGS", "\\Seen")
                    continue

                # Attachment note थप्ने
                if has_att:
                    reply += f"\n\n📎 तपाईंले {len(att_list)} attachment(s) पठाउनुभयो: {', '.join(att_list[:3])}"

                # Reply पठाउने
                reply_subject = _build_reply_subject(subject)
                sent = send_email(sender_email, reply_subject, reply)

                if sent:
                    stats["processed"] += 1

                    # Audit log — email processed
                    log_event(
                        event_type="email_received",
                        email=sender_email,
                        username=sender_name,
                        action="auto_reply",
                        status="success",
                        details={
                            "subject": subject[:200],
                            "attachments": att_list,
                            "body_length": len(body)
                        }
                    )
                else:
                    stats["errors"] += 1
                    log_event(
                        event_type="email_received",
                        email=sender_email,
                        username=sender_name,
                        action="auto_reply",
                        status="fail",
                        details={"subject": subject[:200]}
                    )

                # Mark as read
                if MARK_AS_READ:
                    mail.store(num, "+FLAGS", "\\Seen")

                print(f"{C.CYAN}{'─'*60}{C.END}\n")

            except Exception as e:
                logging.error(f"Email process error: {e}")
                log_error(f"Email error: {e}")
                stats["errors"] += 1
                try:
                    mail.store(num, "+FLAGS", "\\Seen")
                except Exception:
                    pass

        if stats["processed"] > 0 or stats["skipped_spam"] > 0:
            print(f"\n{C.GREEN}{C.BOLD}📊 Summary:{C.END}")
            print(f"   ✅ Processed: {stats['processed']}")
            print(f"   ⏭️  Spam: {stats['skipped_spam']}")
            print(f"   ⏭️  Empty: {stats['skipped_empty']}")
            print(f"   ⏭️  Self: {stats['skipped_self']}")
            if stats["attachments"]:
                print(f"   📎 Attachments: {stats['attachments']}")
            if stats["errors"]:
                print(f"   ❌ Errors: {stats['errors']}")
            print()

        return stats

    except imaplib.IMAP4.error as e:
        logging.error(f"IMAP error: {e}")
        log_error(f"IMAP error: {e}")
        return stats
    except Exception as e:
        logging.error(f"Email check error: {e}")
        log_error(f"Email check error: {e}")
        return stats
    finally:
        try:
            if mail:
                mail.logout()
        except Exception:
            pass


# ============================================================
# Email Watcher (Background + Graceful shutdown)
# ============================================================
_shutdown_flag = {"stop": False}


def _signal_handler(sig, frame):
    print(f"\n\n{C.YELLOW}👋 Shutdown signal प्राप्त — बन्द गर्दै...{C.END}")
    _shutdown_flag["stop"] = True


def run_email_watcher(interval=60):
    """Background मा emails check गर्ने"""
    log_header("📧 PDF Brain — Email Watcher (AI Spam Filter सहित)")

    if not EMAIL or not PASSWORD:
        log_error(".env मा EMAIL र EMAIL_PASSWORD सेट गर्नुहोस्")
        return

    print(f"{C.BOLD}📧 Email:{C.END} {EMAIL}")
    print(f"{C.BOLD}⏱️  Interval:{C.END} {interval}s")
    print(f"{C.BOLD}🔍 Max per check:{C.END} {MAX_EMAILS_PER_CHECK}")
    print(f"{C.BOLD}🤖 AI Spam Filter:{C.END} {'✅ ON' if USE_AI_SPAM_FILTER else '❌ OFF'}")
    print(f"{C.BOLD}🛑 Stop:{C.END} Ctrl + C")
    print()

    # Signal handler
    try:
        signal.signal(signal.SIGINT, _signal_handler)
    except Exception:
        pass

    # SMTP test
    log_info("Testing SMTP connection...")
    try:
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10) as s:
                s.login(EMAIL, PASSWORD)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
                s.starttls()
                s.login(EMAIL, PASSWORD)
        log_success("SMTP OK")
    except Exception as e:
        log_error(f"SMTP FAIL: {e}")
        return

    # IMAP test
    log_info("Testing IMAP connection...")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, timeout=10)
        mail.login(EMAIL, PASSWORD)
        mail.logout()
        log_success("IMAP OK")
    except Exception as e:
        log_error(f"IMAP FAIL: {e}")
        return

    print(f"\n{C.GREEN}{C.BOLD}🚀 Watcher सुरु भयो{C.END}\n")

    cycle = 0
    while not _shutdown_flag["stop"]:
        try:
            cycle += 1
            print(f"{C.BOLD}{'─'*60}{C.END}")
            print(f"{C.CYAN}🔄 Cycle #{cycle} — {datetime.now().strftime('%H:%M:%S')}{C.END}")
            print(f"{C.BOLD}{'─'*60}{C.END}")

            stats = check_new_emails()

            if stats["total"] == 0:
                print(f"{C.BLUE}📭 कुनै नयाँ email छैन{C.END}")
            elif stats["processed"] == 0 and stats["total"] > 0:
                print(f"{C.BLUE}💤 {stats['total']} emails — सबै skip भए{C.END}")

            # Sleep (interruptible)
            print(f"\n⏱️  {interval}s पर्खँदै... (Ctrl+C बन्द गर्न)\n")
            slept = 0
            while slept < interval and not _shutdown_flag["stop"]:
                time.sleep(1)
                slept += 1

        except KeyboardInterrupt:
            print(f"\n\n{C.YELLOW}👋 Watcher बन्द गर्दै...{C.END}")
            break
        except Exception as e:
            logging.error(f"Watcher error: {e}")
            log_error(f"Watcher error: {e}")
            time.sleep(10)

    print(f"{C.GREEN}✅ Watcher बन्द भयो।{C.END}")


# ============================================================
# CLI
# ============================================================
if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "watch"

    if cmd == "test":
        log_header("🧪 Test Email")
        if not EMAIL:
            log_error(".env मा EMAIL सेट गर्नुहोस्")
        else:
            print(f"📤 To: {EMAIL}")
            success = send_email(
                EMAIL,
                "PDF Brain Test",
                "यो PDF Brain बाट test email हो। ✅\n\nसबै काम गर्दैछ!"
            )
            if success:
                log_success("आफ्नो Inbox जाँच्नुहोस्!")

    elif cmd == "check":
        log_header("📬 एकचोटि Check")
        stats = check_new_emails()
        if stats["total"] == 0:
            log_info("कुनै नयाँ email छैन")

    elif cmd == "debug":
        log_header("🔍 Debug Mode")

        try:
            mail = imaplib.IMAP4_SSL(IMAP_HOST)
            mail.login(EMAIL, PASSWORD)
            mail.select("inbox")

            status, msgs = mail.search(None, "UNSEEN")
            email_ids = msgs[0].split()

            print(f"📬 UNSEEN: {len(email_ids)}\n")

            for num in email_ids[-3:]:
                status, data = mail.fetch(num, "(RFC822)")
                msg = email.message_from_bytes(data[0][1])

                sender_email, sender_name = _extract_sender(msg)
                subject = msg["Subject"]
                body = get_email_body(msg)
                has_att, att_list = _has_attachments(msg)

                spam, reason = is_spam(sender_email, subject, body[:200])

                print(f"{'='*60}")
                print(f"From: {sender_email} ({sender_name})")
                print(f"Subject: {subject}")
                print(f"Body length: {len(body)}")
                print(f"Body: {body[:300]}")
                print(f"Attachments: {att_list if has_att else 'None'}")
                print(f"Is spam: {spam} — {reason}")
                print(f"{'='*60}\n")

            mail.logout()
        except Exception as e:
            log_error(f"Debug error: {e}")

    elif cmd == "clean":
        log_header("🧹 Cleanup UNSEEN emails")

        confirm = input(f"सबै UNSEEN emails mark as read गर्ने? (yes/no): ")
        if confirm.lower() != "yes":
            print("रद्द गरियो")
            sys.exit()

        try:
            mail = imaplib.IMAP4_SSL(IMAP_HOST)
            mail.login(EMAIL, PASSWORD)
            mail.select("inbox")

            status, msgs = mail.search(None, "UNSEEN")
            email_ids = msgs[0].split()

            print(f"📬 {len(email_ids)} emails mark as read गर्दै...")

            for num in email_ids:
                mail.store(num, "+FLAGS", "\\Seen")

            mail.logout()
            log_success(f"{len(email_ids)} emails cleaned!")
        except Exception as e:
            log_error(f"Clean error: {e}")

    elif cmd == "watch":
        run_email_watcher(interval=EMAIL_CHECK_INTERVAL)

    else:
        print("Usage:")
        print("  python email_server.py          — Watcher चलाउने (default)")
        print("  python email_server.py test     — Test email पठाउने")
        print("  python email_server.py check    — एकचोटि check")
        print("  python email_server.py debug    — Debug mode")
        print("  python email_server.py clean    — UNSEEN emails clean")


# ============================================================
# send_email_with_attachment — Auto-Pilot Agent का लागि
# ============================================================
from email.message import EmailMessage


def send_email_with_attachment(to, subject, body, attachment_path=None):
    """Attachment सहित इमेल पठाउनुहोस् (retry सहित)"""
    sender = os.getenv("SMTP_USER") or os.getenv("EMAIL", "")
    password = (os.getenv("SMTP_PASS") or os.getenv("EMAIL_PASSWORD", "")).replace(" ", "")
    from_name = os.getenv("FROM_NAME", "PDF Brain")

    if not sender or not password:
        log_error("SMTP config .env मा छैन")
        return False

    try:
        msg = EmailMessage()
        msg["From"] = formataddr((from_name, sender))
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                file_data = f.read()
            filename = os.path.basename(attachment_path)
            msg.add_attachment(
                file_data,
                maintype="application",
                subtype="octet-stream",
                filename=filename
            )

        # Retry
        last_error = None
        for attempt in range(1, 3):
            try:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=20) as smtp:
                    smtp.login(sender, password)
                    smtp.send_message(msg)
                log_success(f"Attachment email पठाइयो: {to}")
                return True
            except Exception as e:
                last_error = e
                logging.error(f"Attachment send attempt {attempt} failed: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)

        log_error(f"Attachment email failed: {last_error}")
        return False

    except Exception as e:
        logging.error(f"Attachment compose error: {e}")
        log_error(f"Attachment compose error: {e}")
        return False