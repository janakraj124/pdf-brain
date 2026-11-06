# whatsapp_server.py — Powerful Version
import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from message_handler import handle_message

load_dotenv()

app = Flask(__name__)


@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """WhatsApp message handle"""
    
    incoming = request.form.get("Body", "").strip()
    sender = request.form.get("From", "")
    sender_name = request.form.get("ProfileName", "User")
    
    # WhatsApp number → user_id
    user_id = f"wa_{sender.replace('whatsapp:', '').replace('+', '')}"
    
    print(f"\n📱 {sender_name} ({sender}): {incoming}")
    
    if not incoming:
        return str(MessagingResponse())
    
    # Process via shared handler
    reply = handle_message(user_id, incoming)
    
    if not reply:
        reply = "🤔 केही समस्या भयो। फेरि try गर्नुहोस्।"
    
    # WhatsApp limit (1600 chars)
    if len(reply) > 1550:
        reply = reply[:1550] + "\n\n_(छोटोको लागि फेरि सोध्नुहोस्)_"
    
    resp = MessagingResponse()
    resp.message(reply)
    return str(resp)


@app.route("/", methods=["GET"])
def home():
    return """
    <h1>🧠 PDF Brain WhatsApp Server</h1>
    <p>✅ चालु छ</p>
    <p>Webhook: <code>/whatsapp</code></p>
    """


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "service": "PDF Brain WhatsApp"}


if __name__ == "__main__":
    print("=" * 60)
    print("📱 PDF Brain — WhatsApp Server")
    print("=" * 60)
    print(f"🌐 Webhook: http://localhost:5000/whatsapp")
    print(f"🛑 Ctrl + C बन्द गर्न")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=True)