# email_helper.py — PDF Brain (Email + OTP + Reset Link)
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# 🔗 RESET LINK EMAIL (१ घण्टा valid)
# ============================================================
def send_reset_email(to_email, reset_link, username=""):
    """Reset link email पठाउने"""
    try:
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_pass = os.getenv("SMTP_PASS", "")
        from_name = os.getenv("FROM_NAME", "PDF Brain")

        if not smtp_user or not smtp_pass:
            return {"success": False, "error": "SMTP config .env मा छैन"}

        msg = EmailMessage()
        msg["From"] = f"{from_name} <{smtp_user}>"
        msg["To"] = to_email
        msg["Subject"] = "🔑 PDF Brain — Password Reset"

        # ✅ पहिले plain text
        msg.set_content(
            f"Password reset link: {reset_link}\n\n"
            f"यो link १ घण्टा valid छ।\n\n"
            f"यदि तपाईंले अनुरोध गर्नुभएको छैन भने, यो email बेवास्ता गर्नुहोस्।"
        )

        # ✅ त्यसपछि HTML
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #667eea;">🔑 Password Reset</h2>
            <p>नमस्ते {username or "प्रयोगकर्ता"},</p>
            <p>तपाईंले PDF Brain मा password reset अनुरोध गर्नुभयो। तलको link मा क्लिक गरेर नयाँ password सेट गर्नुहोस्:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                    🔓 Password Reset गर्नुहोस्
                </a>
            </p>
            <p style="color: #666; font-size: 0.9em;">⚠️ यो link <b>१ घण्टा</b> मात्र valid छ।</p>
            <p style="color: #666; font-size: 0.9em;">यदि तपाईंले अनुरोध गर्नुभएको छैन भने, यो email बेवास्ता गर्नुहोस्।</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 0.8em;">🧠 PDF Brain v52.0 · Made with ❤️ in Nepal</p>
        </div>
        """
        msg.add_alternative(html, subtype="html")

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# 🔢 OTP EMAIL (६-अंक, ५ मिनेट valid)
# ============================================================
def send_otp_email(to_email, otp_code, username=""):
    """OTP code email पठाउने"""
    try:
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_pass = os.getenv("SMTP_PASS", "")
        from_name = os.getenv("FROM_NAME", "PDF Brain")

        if not smtp_user or not smtp_pass:
            return {"success": False, "error": "SMTP config .env मा छैन"}

        msg = EmailMessage()
        msg["From"] = f"{from_name} <{smtp_user}>"
        msg["To"] = to_email
        msg["Subject"] = "🔑 PDF Brain — Password Reset Code"

        # ✅ पहिले plain text
        msg.set_content(
            f"तपाईंको password reset code: {otp_code}\n\n"
            f"यो code ५ मिनेट valid छ।\n\n"
            f"यदि तपाईंले अनुरोध गर्नुभएको छैन भने, यो email बेवास्ता गर्नुहोस्।"
        )

        # ✅ त्यसपछि HTML
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #fafbff; border-radius: 16px;">
            <div style="text-align: center; padding: 20px 0;">
                <h1 style="color: #667eea; margin: 0; font-size: 1.8em;">🔑 Password Reset</h1>
                <p style="color: #6b7280; margin-top: 8px;">PDF Brain</p>
            </div>
            
            <div style="background: white; border-radius: 12px; padding: 30px; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);">
                <p style="font-size: 1.05em;">नमस्ते <strong>{username or "प्रयोगकर्ता"}</strong>,</p>
                <p>तपाईंको password reset को लागि यो ६-अंकको code प्रयोग गर्नुहोस्:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <div style="display: inline-block; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px 40px; border-radius: 12px; font-size: 2.5em; font-weight: bold; letter-spacing: 10px; box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);">
                        {otp_code}
                    </div>
                </div>
                
                <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 12px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 0; color: #856404; font-size: 0.9em;">
                        ⏱️ यो code <strong>५ मिनेट</strong> मात्र valid छ।
                    </p>
                </div>
                
                <div style="background: #e7f3ff; border-left: 4px solid #0066cc; padding: 12px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 0; color: #004085; font-size: 0.85em;">
                        🔒 यदि तपाईंले अनुरोध गर्नुभएको छैन भने, यो email बेवास्ता गर्नुहोस् र कसैलाई code नदिनुहोस्।
                    </p>
                </div>
            </div>
            
            <p style="text-align: center; color: #999; font-size: 0.8em; margin-top: 20px;">
                🧠 PDF Brain v52.0 · Made with ❤️ in Nepal
            </p>
        </div>
        """
        msg.add_alternative(html, subtype="html")

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# 📧 GENERAL EMAIL (वैकल्पिक — broadcast को लागि)
# ============================================================
def send_email(to_email, subject, body, username=""):
    """सामान्य email पठाउने"""
    try:
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_pass = os.getenv("SMTP_PASS", "")
        from_name = os.getenv("FROM_NAME", "PDF Brain")

        if not smtp_user or not smtp_pass:
            return {"success": False, "error": "SMTP config .env मा छैन"}

        msg = EmailMessage()
        msg["From"] = f"{from_name} <{smtp_user}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        # ✅ पहिले plain text
        msg.set_content(body)

        # ✅ त्यसपछि HTML
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #667eea;">{subject}</h2>
            <p>नमस्ते {username or "प्रयोगकर्ता"},</p>
            <div style="line-height: 1.7;">{body.replace(chr(10), "<br>")}</div>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 0.8em;">🧠 PDF Brain v52.0 · Made with ❤️ in Nepal</p>
        </div>
        """
        msg.add_alternative(html, subtype="html")

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# 🧪 TEST
# ============================================================
if __name__ == "__main__":
    print("🧪 Testing email_helper.py...\n")

    # Test OTP (email आफ्नो राख्नुहोस्)
    test_email = os.getenv("SMTP_USER", "")
    if test_email:
        print(f"Testing OTP email to: {test_email}")
        result = send_otp_email(test_email, "123456", "Test User")
        print(f"OTP Email: {'✅' if result['success'] else '❌'} — {result.get('error', 'Sent!')}")
    else:
        print("⚠️ SMTP_USER .env मा छैन — test गर्न सकिएन")