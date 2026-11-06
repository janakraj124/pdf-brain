# user_answer.py — Universal Powerful Edition
import os
import time
from dotenv import load_dotenv
from google import genai
from user_vector_store import user_search

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.5-flash-lite"


def detect_question_type(question):
    """प्रश्न को प्रकार पहिचान गर्ने"""
    q = question.lower().strip()
    
    # Count प्रश्न
    if any(kw in q for kw in ["कति", "how many", "count", "number of", "total"]):
        return "count"
    
    # List प्रश्न
    if any(kw in q for kw in ["list", "सूची", "सबै", "all", "देखाउनु", "show"]):
        return "list"
    
    # Summary प्रश्न
    if any(kw in q for kw in ["summary", "सारांश", "के छ", "what is", "बारेमा", "about", "describe"]):
        return "summary"
    
    # Yes/No प्रश्न
    if any(kw in q for kw in ["हो?", "हो कि", "is it", "is this", "are there", "छ कि"]):
        return "yesno"
    
    # Comparison
    if any(kw in q for kw in ["कुन", "which", "compare", "तुलना", "भन्दा"]):
        return "comparison"
    
    # Default: specific
    return "specific"


def get_conversation_context(username):
    """User को पुरानो conversation context"""
    try:
        from message_handler import get_user
        user_data = get_user(f"web_{username}")
        history = user_data.get("history", [])[-6:]  # Last 3 pairs
        
        if not history:
            return ""
        
        history_text = "\n\n📜 पहिलेको कुराकानी (context को लागि):\n"
        for h in history:
            role = "👤 User" if h["role"] == "user" else "🧠 AI"
            content = h.get("content", "")[:200]
            history_text += f"{role}: {content}\n"
        
        return history_text
    except Exception:
        return ""


def build_powerful_prompt(context, question, history_text="", q_type="specific", doc_type="general"):
    """Document type + Question type अनुसार smart prompt"""
    
    # Type-specific guidelines
    type_guides = {
        "cv": """
📋 **CV/Resume को लागि:**
- नाम, contact, email, phone खोज्नुहोस्
- Experience, education, skills
- पद, कम्पनी, duration
- Certifications, awards""",
        
        "invoice": """
💰 **Invoice/Bill को लागि:**
- Invoice number, date, due date
- Vendor, customer
- Items, quantity, price
- Total, tax, discount
- Payment terms""",
        
        "letter": """
✉️ **Letter को लागि:**
- Sender, recipient
- Date
- Subject/purpose
- Main message
- Action requested""",
        
        "contract": """
📜 **Contract को लागि:**
- Parties (who)
- Effective date, duration
- Terms, conditions
- Payment, obligations
- Termination clauses""",
        
        "certificate": """
🏆 **Certificate को लागि:**
- Recipient name
- Award/degree
- Issuing organization
- Date
- Achievement details""",
        
        "report": """
📊 **Report को लागि:**
- Title, author, date
- Executive summary
- Key findings
- Data, statistics
- Recommendations""",
        
        "prescription": """
💊 **Prescription को लागि:**
- Patient info
- Medicines (name, dosage)
- Frequency, duration
- Instructions
- Doctor info""",
        
        "medical": """
🏥 **Medical Document को लागि:**
- Patient info
- Symptoms, diagnosis
- Treatment, medicines
- Test results
- Doctor's notes""",
        
        "book": """
📚 **Book को लागि:**
- Title, author
- Chapters, topics
- Main themes
- Key concepts
- Summary""",
        
        "academic": """
🎓 **Academic Document को लागि:**
- Title, author
- Research question
- Methodology
- Findings
- Conclusion""",
        
        "legal": """
⚖️ **Legal Document को लागि:**
- Case/parties
- Facts
- Legal issues
- Ruling/decision
- Sections cited""",
        
        "general": """
📄 **General Document को लागि:**
- मुख्य विषय के?
- Important details
- नाम, dates, numbers
- जे सोधे त्यो भन्नुहोस्"""
    }
    
    doc_guide = type_guides.get(doc_type, type_guides["general"])
    
    prompt = f"""तपाईं एक **बुद्धिमान, universal AI सहायक** हुनुहुन्छ।
जसको जस्तो document भएपनि, जे प्रश्न सोधेपनि **सही जवाफ** दिनुहोस्।

{history_text}

📋 **Document बाट जानकारी:**
{context}

❓ **User को प्रश्न:** {question}

🎯 **Document Type: {doc_type.upper()}**

{doc_guide}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **Universal नियमहरू:**

**১. जे सोधे पनि जवाफ दिनुहोस्:**
- General ("के छ?") → Summary दिनुहोस्
- Specific → Exact जवाफ
- List → Bullet points
- Count → Number सहित

**২. Format:**
- **Bold** मुख्य कुरा
- • Bullet points
- Numbers स्पष्ट

**৩. भाषा:**
- User को भाषा अनुसार

**৪. Anti-Hallucination:**
- Document मा भएको मात्र
- नाम, dates, numbers exactly

**৫. सधैं सहयोगी:**
- "भेटिएन" मात्र जब साँच्चै छैन
- Partial भए पनि दिनुहोस्

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

अब जवाफ दिनुहोस्:"""
    
    return prompt


def answer_user_question(username, question, max_retries=3):
    """
    User को PDF मा प्रश्न सोध्ने (Universal Powerful)
    
    जसको जस्तो PDF भएपनि जवाफ दिन्छ।
    """
    start_time = time.time()
    
    # Validate
    if not question or len(question.strip()) < 2:
        return {"answer": "❓ कृपया प्रश्न लेख्नुहोस्।", "sources": []}
    
    # Search user PDFs
    try:
        docs, metas = user_search(username, question, n=6)
    except Exception as e:
        return {"answer": f"❌ Search error: {e}", "sources": []}
    
    if not docs:
        return {
            "answer": (
                "⚠️ **तपाईंको PDF मा यो जानकारी भेटिएन।**\n\n"
                "💡 **के गर्ने:**\n"
                "1. PDF सही upload भयो?\n"
                "2. Sidebar → **PDF हाल्नुहोस्**\n"
                "3. फरक शब्दमा सोध्नुहोस्\n"
                "4. Specific प्रश्न सोध्नुहोस्"
            ),
            "sources": []
        }
    
    # Context
    context = "\n\n━━━━━━━━━━━━━━━━━━\n\n".join(docs)
    sources = list(set([m["source"] for m in metas]))
    
    # Question type detect
    q_type = detect_question_type(question)
    
    # History
    history_text = get_conversation_context(username)
    
    # Build powerful prompt
    prompt = build_powerful_prompt(
        context=context,
        question=question,
        history_text=history_text,
        q_type=q_type
    )
    
    # AI Call with Retry
    answer_text = "❌ AI जवाफ दिन सकेन। फेरि प्रयास गर्नुहोस्।"
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )
            answer_text = response.text
            break
        except Exception as e:
            err = str(e)
            
            if ("503" in err or "429" in err) and attempt < max_retries - 1:
                time.sleep((attempt + 1) * 3)
                continue
            
            if "429" in err:
                answer_text = "⏳ **Quota सकियो।** भोलि try गर्नुहोस्।"
            elif "503" in err:
                answer_text = "⏳ **Server व्यस्त।** १ मिनेट पछि try।"
            else:
                answer_text = f"❌ Error: {str(e)[:200]}"
            break
    
    elapsed = time.time() - start_time
    
    # Save to history
    try:
        from message_handler import add_to_history
        add_to_history(f"web_{username}", "user", question)
        add_to_history(f"web_{username}", "assistant", answer_text)
    except Exception:
        pass
    
    # Analytics
    try:
        from analytics import log_query
        log_query(f"user_{username}", question, answer_text, elapsed, sources)
    except Exception:
        pass
    
    return {
        "answer": answer_text,
        "sources": sources
    }