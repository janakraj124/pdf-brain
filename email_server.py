# email_server.py — Powerful Edition
import os
import re
import ssl
import time
import email
import smtplib
import imaplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
from pymsgbox import password
from answer import answer_question

load_dotenv()

# ============================================================
# Configuration
# ============================================================
EMAIL = os.getenv("EMAIL", "")
PASSWORD = os.getenv("EMAIL_PASSWORD", "").replace(" ", "")
EMAIL_CHECK_INTERVAL = int(os.getenv("EMAIL_CHECK_INTERVAL", "60"))

SMTP_HOST = "smtp.gmail.com"
IMAP_HOST = "imap.gmail.com"

# Email processing limits
MAX_EMAILS_PER_CHECK = 5   # एकचोटि 5 मात्र
MAX_BODY_LENGTH = 1500      # Body limit
MIN_BODY_LENGTH = 5         # यो भन्दा छोटो skip
MARK_AS_READ = True         # Process पछि read गर्ने

# Skip keywords — यी spam/promo छन्
SKIP_SENDER_KEYWORDS = [
    "no-reply", "noreply", "do_not_reply", "donotreply",
    "do-not-reply", "notification", "newsletter",
    "marketing", "promo", "info@", "support@",
    "bounce", "mailer", "auto-confirm",
    "binance", "coinbase", "kraken",
    "facebookmail", "linkedin", "twitter",
    "instagram", "youtube", "google-noreply",
    "microsoft", "apple", "amazon",
    "verify", "confirm", "security",
    "no_reply", "noreply", "alert"
]

SKIP_SUBJECT_KEYWORDS = [
    "unsubscribe", "verify your", "confirm your",
    "security alert", "suspicious", "suspicious activity",
    "password reset", "new login", "login attempt",
    "order confirmed", "shipping", "delivery",
    "newsletter", "weekly", "daily digest",
    "promotion", "offer", "sale", "discount",
    "your receipt", "your invoice", "your statement",
    "bear and bull", "earn more", "bitcoin",
    "crypto", "investment"
]


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
# Send Email
# ============================================================
def send_email(to, subject, body):
    """Email पठाउने — HTML + Plain text"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"PDF Brain <{EMAIL}>"
        msg["To"] = to
        
        # Plain text
        text_part = MIMEText(body, "plain", "utf-8")
        
        # HTML version
        body_html = body.replace("\n", "<br>")
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', system-ui, sans-serif; 
                    line-height: 1.6; color: #333; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #667eea, #764ba2); 
                       color: white; padding: 25px; border-radius: 12px 12px 0 0;
                       text-align: center; }}
            .header h2 {{ margin: 0; font-size: 1.8em; }}
            .header small {{ opacity: 0.9; }}
            .content {{ background: #ffffff; padding: 30px; 
                        border-left: 1px solid #eee; border-right: 1px solid #eee; }}
            .footer {{ background: #f8f9fa; padding: 20px; 
                       border-radius: 0 0 12px 12px; text-align: center;
                       color: #666; font-size: 0.9em;
                       border: 1px solid #eee; }}
            .btn {{ display: inline-block; padding: 10px 20px; 
                    background: #667eea; color: white; 
                    text-decoration: none; border-radius: 6px; }}
        </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🧠 PDF Brain</h2>
                    <small>AI-powered PDF Assistant</small>
                </div>
                <div class="content">
                    {body_html}
                </div>
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
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        with smtplib.SMTP_SSL(SMTP_HOST, 465, timeout=15) as server:
            server.login(EMAIL, PASSWORD)
            server.send_message(msg)
        
        log_success(f"Email पठाइयो: {to}")
        return True
    except Exception as e:
        log_error(f"Email send error: {e}")
        return False


# ============================================================
# Extract Email Body (सफा)
# ============================================================
def get_email_body(msg):
    """Email बाट सफा text निकाल्ने (HTML + quote सफा)"""
    body = ""
    
    # Multipart handling
    if msg.is_multipart():
        # पहिले text/plain try
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
    
    # Quote हटाउने
    body = _remove_quotes(body)
    
    # Whitespace clean
    body = re.sub(r'\s+', ' ', body).strip()
    
    return body


def _clean_html(html):
    """HTML बाट text मात्र निकाल्ने"""
    # Script + Style हटाउने
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<head[^>]*>.*?</head>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # <br> र <p> लाई newline बनाउने
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</p>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</div>', '\n', html, flags=re.IGNORECASE)
    
    # बाँकी tags हटाउने
    html = re.sub(r'<[^>]+>', ' ', html)
    
    # HTML entities
    entities = {
        '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>',
        '&quot;': '"', '&#39;': "'", '&apos;': "'",
        '&copy;': '©', '&reg;': '®', '&trade;': '™',
        '&hellip;': '...', '&mdash;': '—', '&ndash;': '–'
    }
    for entity, char in entities.items():
        html = html.replace(entity, char)
    
    # Numeric entities
    html = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))) if int(m.group(1)) < 1114111 else '', html)
    
    return html.strip()


def _remove_quotes(body):
    """पुरानो email thread हटाउने"""
    # Common quote patterns
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
# Spam Check
# ============================================================
def is_spam(sender_email, subject):
    """Spam हो कि जाँच्ने"""
    sender_lower = sender_email.lower()
    subject_lower = subject.lower()
    
    # Sender check
    for kw in SKIP_SENDER_KEYWORDS:
        if kw in sender_lower:
            return True, f"sender contains '{kw}'"
    
    # Subject check
    for kw in SKIP_SUBJECT_KEYWORDS:
        if kw in subject_lower:
            return True, f"subject contains '{kw}'"
    
    # Sender pattern
    if sender_lower.endswith("@mail.gmail.com"):
        return True, "system email"
    
    return False, ""


# ============================================================
# Check Emails
# ============================================================
def check_new_emails():
    """नयाँ emails check गरेर auto-reply (message_handler सहित)"""
    from message_handler import handle_message, get_user
    
    stats = {
        "total": 0,
        "processed": 0,
        "skipped_spam": 0,
        "skipped_empty": 0,
        "errors": 0
    }
    
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, timeout=30)
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")
        
        status, messages = mail.search(None, "UNSEEN")
        
        if status != "OK":
            mail.logout()
            return stats
        
        email_ids = messages[0].split()
        stats["total"] = len(email_ids)
        
        if not email_ids:
            mail.logout()
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
                
                # Sender
                sender = msg["From"] or ""
                if "<" in sender:
                    sender_email = sender.split("<")[1].split(">")[0].strip()
                else:
                    sender_email = sender.strip()
                
                if sender_email.lower() == EMAIL.lower():
                    continue
                
                subject = msg["Subject"] or "(कुनै subject छैन)"
                
                # Spam check
                spam, reason = is_spam(sender_email, subject)
                if spam:
                    log_skip(f"Spam ({reason}): {sender_email}")
                    stats["skipped_spam"] += 1
                    mail.store(num, "+FLAGS", "\\Seen")
                    continue
                
                # Body
                body = get_email_body(msg)[:MAX_BODY_LENGTH].strip()
                
                if len(body) < MIN_BODY_LENGTH:
                    log_skip(f"Empty body: {sender_email}")
                    stats["skipped_empty"] += 1
                    mail.store(num, "+FLAGS", "\\Seen")
                    continue
                
                # ⚠️ NEW: User ID
                user_id = f"email_{sender_email}"
                
                print(f"{C.BOLD}📧 From:{C.END} {sender_email}")
                print(f"{C.BOLD}   Subject:{C.END} {subject[:80]}")
                print(f"{C.BOLD}   Body:{C.END} {body[:120]}...")
                print()
                
                # ⚠️ NEW: message_handler प्रयोग
                reply = handle_message(user_id, body)
                
                if not reply:
                    log_skip("Empty response")
                    mail.store(num, "+FLAGS", "\\Seen")
                    continue
                
                # Reply पठाउने
                reply_subject = f"Re: {subject}" if not subject.startswith("Re:") else subject
                send_email(sender_email, reply_subject, reply)
                
                stats["processed"] += 1
                
                # Mark as read
                if MARK_AS_READ:
                    mail.store(num, "+FLAGS", "\\Seen")
                
                print(f"{C.CYAN}{'─'*60}{C.END}\n")
                
            except Exception as e:
                log_error(f"Email error: {e}")
                stats["errors"] += 1
                try:
                    mail.store(num, "+FLAGS", "\\Seen")
                except Exception:
                    pass
        
        mail.logout()
        
        if stats["processed"] > 0:
            print(f"\n{C.GREEN}{C.BOLD}📊 Summary:{C.END}")
            print(f"   ✅ Processed: {stats['processed']}")
            print(f"   ⏭️  Spam: {stats['skipped_spam']}")
            print(f"   ⏭️  Empty: {stats['skipped_empty']}")
            if stats["errors"]:
                print(f"   ❌ Errors: {stats['errors']}")
            print()
        
        return stats
        
    except imaplib.IMAP4.error as e:
        log_error(f"IMAP error: {e}")
        return stats
    except Exception as e:
        log_error(f"Email check error: {e}")
        return stats


# ============================================================
# Email Watcher (Background)
# ============================================================
def run_email_watcher(interval=60):
    """Background मा emails check गर्ने"""
    log_header("📧 PDF Brain — Email Watcher")
    
    if not EMAIL or not PASSWORD:
        log_error(".env मा EMAIL र EMAIL_PASSWORD सेट गर्नुहोस्")
        return
    
    print(f"{C.BOLD}📧 Email:{C.END} {EMAIL}")
    print(f"{C.BOLD}⏱️  Interval:{C.END} {interval}s")
    print(f"{C.BOLD}🔍 Max per check:{C.END} {MAX_EMAILS_PER_CHECK}")
    print(f"{C.BOLD}🛑 Stop:{C.END} Ctrl + C")
    print()
    
    # Connection test
    log_info("Testing SMTP connection...")
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, 465, timeout=10) as s:
            s.login(EMAIL, PASSWORD)
        log_success("SMTP OK")
    except Exception as e:
        log_error(f"SMTP FAIL: {e}")
        return
    
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
    while True:
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
            
            print(f"\n⏱️  {interval}s पर्खँदै... (Ctrl+C बन्द गर्न)\n")
            time.sleep(interval)
            
        except KeyboardInterrupt:
            print(f"\n\n{C.YELLOW}👋 Watcher बन्द गर्दै...{C.END}")
            break
        except Exception as e:
            log_error(f"Watcher error: {e}")
            time.sleep(10)


# ============================================================
# CLI
# ============================================================
if __name__ == "__main__":
    import sys
    
    cmd = sys.argv[1] if len(sys.argv) > 1 else "watch"
    
    if cmd == "test":
        # Test email पठाउने
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
        # एकचोटि check
        log_header("📬 एकचोटि Check")
        stats = check_new_emails()
        
        if stats["total"] == 0:
            log_info("कुनै नयाँ email छैन")
    
    elif cmd == "debug":
        # Debug mode — पहिलो 3 emails को details
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
                
                sender = msg["From"]
                subject = msg["Subject"]
                body = get_email_body(msg)
                
                spam, reason = is_spam(sender, subject)
                
                print(f"{'='*60}")
                print(f"From: {sender}")
                print(f"Subject: {subject}")
                print(f"Body length: {len(body)}")
                print(f"Body: {body[:300]}")
                print(f"Is spam: {spam} — {reason}")
                print(f"{'='*60}\n")
            
            mail.logout()
        except Exception as e:
            log_error(f"Debug error: {e}")
    
    elif cmd == "clean":
        # सबै UNSEEN mark as read (cleanup)
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
        # Default — watcher चलाउने
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
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
import os
import ssl

def send_email_with_attachment(to, subject, body, attachment_path=None):
    """Attachment सहित इमेल पठाउनुहोस्"""
    # ⚠️ तपाईंको email_server.py मा भएको SMTP config अनुसार मिलाउनुहोस्
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    sender = os.getenv("SMTP_USER", "")       # ⚠️ आफ्नो Gmail
    password = os.getenv("SMTP_PASS", "")       # ⚠️ App Password
    FROM_NAME = os.getenv("FROM_NAME", "PDF Brain")

    try:
        msg = EmailMessage()
        msg["From"] = formataddr((FROM_NAME, sender))
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                file_data = f.read()
            filename = os.path.basename(attachment_path)
            msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=filename)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
            
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False