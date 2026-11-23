# system_tools.py — Cost Tracking & Quality Checker
import os
import sqlite3
from datetime import datetime
from google import genai
from dotenv import load_dotenv

load_dotenv()
DB_FILE = "pdf_brain.db"

# ============================================================
# 💰 COST TRACKING
# ============================================================
def init_cost_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cost_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        service TEXT,
        amount REAL,
        timestamp TEXT
    )''')
    conn.commit()
    conn.close()

init_cost_db()

def track_cost(username, service="Gemini", amount=0.0001):
    """एक पटक API प्रयोग गर्दा खर्च रेकर्ड गर्ने"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO cost_tracking (username, service, amount, timestamp) VALUES (?, ?, ?, ?)",
                  (username, service, amount, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[COST ERROR] {e}")

def get_user_cost(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT SUM(amount) FROM cost_tracking WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row and row[0] else 0.0

def get_total_cost():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT SUM(amount) FROM cost_tracking")
    row = c.fetchone()
    conn.close()
    return row[0] if row and row[0] else 0.0

# ============================================================
# ✅ QUALITY CHECKER
# ============================================================
def check_document_quality(file_path):
    """PDF वा टेबलको गुणस्तर जाँच्ने (AI)"""
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # यदि PDF हो भने
        if file_path.lower().endswith(".pdf"):
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = "".join([page.extract_text() for page in reader.pages[:3]]) # पहिलो ३ पेज
            
            prompt = f"""
            You are a Quality Checker AI.
            Analyze this document text and provide a brief report in Nepali:
            1. के यो फन्ट बिग्रेको छ वा पढ्न गाह्रो छ?
            2. के यसमा कुनै गोप्य जानकारी (Password, OTP) छ?
            3. समग्र गुणस्तर कस्तो छ?

            Text: {text[:3000]}
            """
            response = client.models.generate_content(model="gemini-3.5-flash-lite", contents=prompt)
            return {"success": True, "report": response.text}
            
        elif file_path.lower().endswith(".csv"):
            import pandas as pd
            df = pd.read_csv(file_path)
            
            # आधारभूत जाँच
            missing_values = df.isnull().sum().sum()
            duplicates = df.duplicated().sum()
            
            report = f"📊 **Data Quality Report**\n\n"
            report += f"- **Total Rows:** {len(df)}\n"
            report += f"- **Missing Values:** {missing_values}\n"
            report += f"- **Duplicate Rows:** {duplicates}\n"
            if missing_values > 0 or duplicates > 0:
                report += "\n⚠️ **Warning:** यो डाटामा केही कमी छन्, कृपया सफा गर्नुहोस्।"
            else:
                report += "\n✅ डाटा एकदमै सफा छ!"
            
            return {"success": True, "report": report}
        else:
            return {"success": False, "error": "यो फाइल फर्म्याट समर्थित छैन।"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}