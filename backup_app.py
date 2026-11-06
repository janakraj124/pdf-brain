# app.py — PDF Brain v26.0 (Ultimate Messenger Style UI)
import os
import csv
import io
import json
import time
import uuid
from datetime import datetime
import pandas as pd
import streamlit as st
from answer import answer_question
from sticky_header import render_sticky_header

# ============================================================
# Page Config
# ============================================================
st.set_page_config(
    page_title="PDF Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# Language Dictionary
# ============================================================
UI_TEXT = {
    "ne": {
        "chat_tab": "💬 Chat", "docs_tab": "📄 Documents", "image_tab": "🖼️ Image", "table_tab": "📊 Table + Chart",
        "chat_welcome": "नमस्ते! के सोध्नु छ?", "chat_hint": "तल chat box मा प्रश्न लेख्नुहोस्",
        "chat_input": "प्रश्न लेख्नुहोस् वा 🎤 थिच्नुहोस्...", "queries": "queries", "no_tags": "कोही छैन",
        "logout": "🚪 Logout", "ui_language": "UI भाषा", "database_ready": "Database तयार", "database_missing": "Database छैन",
        "actions": "Actions", "rebuild": "🔄 Rebuild", "chat_clear": "➕ New Chat", "export_chat": "💾 Export Chat",
        "no_chat": "कुनै chat छैन", "voice_settings": "🎤 Voice Settings", "auto_speak": "🔊 Auto-speak",
        "input_lang": "🎤 Input भाषा", "output_lang": "🔊 Output भाषा", "doc_tags": "🏷️ Document Tags",
        "chat_tag_filter": "Tag Filter", "filter_remove": "✖ हटाउनुहोस्", "filter_active": "Tag Filter Active",
        "filter_hint": "यी tags भएका PDF मा मात्र खोजिन्छ", "no_tags_available": "कुनै tags छैन",
        "admin_panel": "👑 Admin Panel", "users": "users", "deleted": "हटाइयो",
        "my_docs": "मेरो Documents", "upload_doc": "नयाँ Document Upload", "upload_hint": "PDF, DOCX, Image, TXT — कुनै पनि",
        "upload_process": "📤 Upload + Process", "uploading": "Upload हुँदै...", "processing": "Process हुँदै...",
        "files_saved": "files save भयो", "ai_ready": "AI तयार!", "my_files": "मेरा Files", "no_files": "कुनै document छैन।",
        "ask_docs": "💬 Documents बारे सोध्नुहोस्", "ask_hint": "प्रश्न लेख्नुहोस् वा 🎤 थिच्नुहोस्",
        "ask_placeholder": "जस्तै: यो document कसको हो?", "ask_btn": "🔍 सोध्नुहोस्", "clear_btn": "🗑️ Clear",
        "your_question": "तपाईंको प्रश्न", "ai_answer": "AI जवाफ", "thinking": "सोच्दै...", "analyzing": "विश्लेषण...",
        "image_analysis": "Image Analysis", "image_hint": "जस्तो सुकै image — AI ले बुझ्छ", "upload_image": "Image हाल्नुहोस्",
        "analysis_type": "Analysis प्रकार", "analyze_btn": "🔍 Analyze", "delete_btn": "🗑️ हटाउनुहोस्",
        "result": "परिणाम", "upload_prompt": "👈 Image upload गर्नुहोस्", "image_question": "💬 Image बारे सोध्नुहोस्",
        "image_placeholder": "जस्तै: कति amount छ?", "table_chart": "Table + Chart Analysis",
        "table_hint": "PDF, Excel, CSV, Image बाट tables निकालेर Excel मा बदल्नुहोस्", "pdf_select": "File चयन", "tables_found": "tables भेटियो",
        "no_table": "Table भेटिएन", "no_pdf": "docs/ मा File छैन", "no_docs_folder": "docs/ folder छैन",
        "data_tab": "📄 Data", "chart_tab": "📈 Chart", "stats_tab": "📊 Stats", "table_question": "💬 Table बारे सोध्नुहोस्",
        "table_placeholder": "जस्तै: सबैभन्दा ठूलो amount कति?", "voice_label": "🎤 Voice", "ai_label": "🧠 AI जवाफ",
        "made_with": "Made with ❤️ in Nepal", "feedback_thanks": "धन्यवाद!", "copy_btn": "Copy", "speak_btn": "सुन्नुहोस्",
        "like_btn": "राम्रो", "dislike_btn": "नराम्रो", "footer_about": "AI-powered PDF assistant",
        "footer_links": "Links", "voice_hint": "🎤 थिच्नुहोस् → बोल्नुहोस् → Text auto-fill", "download_excel": "📥 Excel Download", "download_csv": "📥 CSV Download",
        "ai_report_btn": "🤖 AI Business Report तयार गर्नुहोस्", "ai_report_title": "🤖 AI Business Analysis Report",
        "ai_report_desc": "AI ले तपाईंको डाटा विश्लेषण गरेर व्यवसायिक रिपोर्ट तयार गर्छ।",
        "upload_new_file": "📤 नयाँ File अपलोड गर्नुहोस् (PDF, Excel, CSV, Image)",
        "select_from_docs": "📁 docs/ फोल्डरबाट छान्नुहोस्", "where_extract": "Table कहाँबाट निकाल्ने?",
        "upload_file_label": "File हाल्नुहोस्", "extract_tables_btn": "📊 Tables निकाल्नुहोस्",
        "extracting": "Tables निकाल्दै...", "table_found_msg": "tables भेटियो —",
        "image_table_msg": "Image बाट Table निकालियो (AI ले पढेको):",
        "download_img_excel": "📥 Download Extracted Table as Excel (.xlsx)",
        "ai_parse_error": "AI ले टेबल सफा फर्म्याटमा दिएन। तलको टेक्स्ट कपी गर्नुहोस्:",
        "download_report": "📥 Download Report (.txt)", "sum": "जोड (Sum)", "avg": "औसत (Avg)", "min": "न्यूनतम (Min)", "max": "अधिकतम (Max)", "no_numeric": "Numeric column छैन",
        "chat_history": "च्याटहरू", "doc_history": "PDF हरू", "img_history": "Image हरू", "table_history": "Table हरू",
        "no_history": "कुनै इतिहास छैन", "online": "अनलाइन", "messages": "सन्देशहरू", "copy_answer": "📋 Copy Answer"
    },
    "en": {
        "chat_tab": "💬 Chat", "docs_tab": "📄 Documents", "image_tab": "🖼️ Image", "table_tab": "📊 Table + Chart",
        "chat_welcome": "Hello! What would you like to ask?", "chat_hint": "Type your question in the chat box below",
        "chat_input": "Type your question or tap 🎤...", "queries": "queries", "no_tags": "None",
        "logout": "🚪 Logout", "ui_language": "UI Language", "database_ready": "Database Ready", "database_missing": "Database Missing",
        "actions": "Actions", "rebuild": "🔄 Rebuild", "chat_clear": "➕ New Chat", "export_chat": "💾 Export Chat",
        "no_chat": "No chat yet", "voice_settings": "🎤 Voice Settings", "auto_speak": "🔊 Auto-speak",
        "input_lang": "🎤 Input Language", "output_lang": "🔊 Output Language", "doc_tags": "🏷️ Document Tags",
        "chat_tag_filter": "Tag Filter", "filter_remove": "✖ Remove Filter", "filter_active": "Tag Filter Active",
        "filter_hint": "Searching only in tagged PDFs", "no_tags_available": "No tags",
        "admin_panel": "👑 Admin Panel", "users": "users", "deleted": "Deleted",
        "my_docs": "My Documents", "upload_doc": "Upload New Document", "upload_hint": "PDF, DOCX, Image, TXT — upload any",
        "upload_process": "📤 Upload + Process", "uploading": "Uploading...", "processing": "Processing...",
        "files_saved": "files saved", "ai_ready": "AI Ready!", "my_files": "My Files", "no_files": "No documents yet.",
        "ask_docs": "💬 Ask about Documents", "ask_hint": "Type question or tap 🎤",
        "ask_placeholder": "e.g., Whose document is this?", "ask_btn": "🔍 Ask", "clear_btn": "🗑️ Clear",
        "your_question": "Your Question", "ai_answer": "AI Answer", "thinking": "Thinking...", "analyzing": "Analyzing...",
        "image_analysis": "Image Analysis", "image_hint": "Any image — AI understands", "upload_image": "Upload Image",
        "analysis_type": "Analysis Type", "analyze_btn": "🔍 Analyze", "delete_btn": "🗑️ Delete",
        "result": "Result", "upload_prompt": "👈 Upload an image", "image_question": "💬 Ask about Image",
        "image_placeholder": "e.g., What is the amount?", "table_chart": "Table + Chart Analysis",
        "table_hint": "Convert Tables from PDF, Excel, CSV, Image to Excel", "pdf_select": "Select File", "tables_found": "tables found",
        "no_table": "No table found", "no_pdf": "No Files in docs/", "no_docs_folder": "docs/ folder missing",
        "data_tab": "📄 Data", "chart_tab": "📈 Chart", "stats_tab": "📊 Stats", "table_question": "💬 Ask about Table",
        "table_placeholder": "e.g., What is the largest amount?", "voice_label": "🎤 Voice", "ai_label": "🧠 AI Answer",
        "made_with": "Made with ❤️ in Nepal", "feedback_thanks": "Thanks!", "copy_btn": "Copy", "speak_btn": "Speak",
        "like_btn": "Like", "dislike_btn": "Dislike", "footer_about": "AI-powered PDF assistant",
        "footer_links": "Links", "voice_hint": "🎤 Tap → Speak → Text auto-fills", "download_excel": "📥 Excel Download", "download_csv": "📥 CSV Download",
        "ai_report_btn": "🤖 Generate AI Business Report", "ai_report_title": "🤖 AI Business Analysis Report",
        "ai_report_desc": "AI analyzes your data and generates a professional business report.",
        "upload_new_file": "📤 Upload New File (PDF, Excel, CSV, Image)",
        "select_from_docs": "📁 Select from docs/ folder", "where_extract": "Where to extract Table from?",
        "upload_file_label": "Upload File", "extract_tables_btn": "📊 Extract Tables",
        "extracting": "Extracting tables...", "table_found_msg": "tables found —",
        "image_table_msg": "Table extracted from Image (AI recognized):",
        "download_img_excel": "📥 Download Extracted Table as Excel (.xlsx)",
        "ai_parse_error": "AI could not format the table properly. Copy the text below:",
        "download_report": "📥 Download Report (.txt)", "sum": "Sum", "avg": "Average", "min": "Minimum", "max": "Maximum", "no_numeric": "No Numeric column",
        "chat_history": "Chats", "doc_history": "PDFs", "img_history": "Images", "table_history": "Tables",
        "no_history": "No history yet", "online": "Online", "messages": "messages", "copy_answer": "📋 Copy Answer"
    },
    "hi": {
        "chat_tab": "💬 Chat", "docs_tab": "📄 Documents", "image_tab": "🖼️ Image", "table_tab": "📊 Table + Chart",
        "chat_welcome": "नमस्ते! क्या पूछना है?", "chat_hint": "नीचे chat box में प्रश्न लिखें",
        "chat_input": "प्रश्न लिखें या 🎤 दबाएं...", "queries": "queries", "no_tags": "कोई नहीं",
        "logout": "🚪 Logout", "ui_language": "UI भाषा", "database_ready": "Database तैयार", "database_missing": "Database नहीं",
        "actions": "Actions", "rebuild": "🔄 Rebuild", "chat_clear": "➕ New Chat", "export_chat": "💾 Export Chat",
        "no_chat": "कोई chat नहीं", "voice_settings": "🎤 Voice Settings", "auto_speak": "🔊 Auto-speak",
        "input_lang": "🎤 Input भाषा", "output_lang": "🔊 Output भाषा", "doc_tags": "🏷️ Document Tags",
        "chat_tag_filter": "Tag Filter", "filter_remove": "✖ हटाएं", "filter_active": "Tag Filter Active",
        "filter_hint": "इन tags वाले PDF में खोज", "no_tags_available": "कोई tags नहीं",
        "admin_panel": "👑 Admin Panel", "users": "users", "deleted": "हटाया",
        "my_docs": "मेरे Documents", "upload_doc": "नया Document Upload", "upload_hint": "PDF, DOCX, Image, TXT — कोई भी",
        "upload_process": "📤 Upload + Process", "uploading": "Upload हो रहा...", "processing": "Process हो रहा...",
        "files_saved": "files save हुए", "ai_ready": "AI तैयार!", "my_files": "मेरी Files", "no_files": "कोई document नहीं।",
        "ask_docs": "💬 Documents के बारे में पूछें", "ask_hint": "प्रश्न लिखें या 🎤 दबाएं",
        "ask_placeholder": "जैसे: यह किसका document है?", "ask_btn": "🔍 पूछें", "clear_btn": "🗑️ Clear",
        "your_question": "आपका प्रश्न", "ai_answer": "AI जवाफ", "thinking": "सोच रहा हूँ...", "analyzing": "विश्लेषण...",
        "image_analysis": "Image Analysis", "image_hint": "कोई भी image — AI समझता है", "upload_image": "Image डालें",
        "analysis_type": "Analysis प्रकार", "analyze_btn": "🔍 Analyze", "delete_btn": "🗑️ हटाएं",
        "result": "परिणाम", "upload_prompt": "👈 Image upload करें", "image_question": "💬 Image के बारे में पूछें",
        "image_placeholder": "जैसे: कितना amount है?", "table_chart": "Table + Chart Analysis",
        "table_hint": "PDF, Excel, CSV, Image से tables निकालें और Excel बनाएं", "pdf_select": "File चुनें", "tables_found": "tables मिले",
        "no_table": "कोई table नहीं", "no_pdf": "docs/ में File नहीं", "no_docs_folder": "docs/ folder नहीं",
        "data_tab": "📄 Data", "chart_tab": "📈 Chart", "stats_tab": "📊 Stats", "table_question": "💬 Table के बारे में पूछें",
        "table_placeholder": "जैसे: सबसे बड़ा amount कितना?", "voice_label": "🎤 Voice", "ai_label": "🧠 AI जवाफ",
        "made_with": "Made with ❤️ in Nepal", "feedback_thanks": "धन्यवाद!", "copy_btn": "Copy", "speak_btn": "सुनें",
        "like_btn": "अच्छा", "dislike_btn": "बुरा", "footer_about": "AI-powered PDF assistant",
        "footer_links": "Links", "voice_hint": "🎤 दबाएं → बोलें → Text auto-fill", "download_excel": "📥 Excel Download", "download_csv": "📥 CSV Download",
        "ai_report_btn": "🤖 AI Business Report बनाएं", "ai_report_title": "🤖 AI Business Analysis Report",
        "ai_report_desc": "AI आपके डेटा का विश्लेषण करके व्यावसायिक रिपोर्ट बनाता है।",
        "upload_new_file": "📤 नई File अपलोड करें (PDF, Excel, CSV, Image)",
        "select_from_docs": "📁 docs/ फोल्डर से चुनें", "where_extract": "Table कहाँ से निकालें?",
        "upload_file_label": "File डालें", "extract_tables_btn": "📊 Tables निकालें",
        "extracting": "Tables निकाल रहे हैं...", "table_found_msg": "tables मिले —",
        "image_table_msg": "Image से Table निकाला गया (AI ने पढ़ा):",
        "download_img_excel": "📥 Download Extracted Table as Excel (.xlsx)",
        "ai_parse_error": "AI table को सही फॉर्मेट में नहीं दे पाया। नीचे दिए गए टेक्स्ट को कॉपी करें:",
        "download_report": "📥 Download Report (.txt)", "sum": "Sum", "avg": "Average", "min": "Minimum", "max": "Maximum", "no_numeric": "कोई Numeric column नहीं",
        "chat_history": "चैट्स", "doc_history": "PDFs", "img_history": "Images", "table_history": "Tables",
        "no_history": "कोई इतिहास नहीं", "online": "ऑनलाइन", "messages": "संदेश", "copy_answer": "📋 Copy Answer"
    }
}

def t(key, lang=None):
    if lang is None: lang = st.session_state.get("ui_lang", "ne")
    return UI_TEXT.get(lang, UI_TEXT["ne"]).get(key, key)

# ============================================================
# Global CSS (Messenger Style UI)
# ============================================================
st.markdown("""
<style>
    .main .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; max-width: 1200px !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%); padding: 8px; border-radius: 14px; border: 1px solid #e8ecf1; box-shadow: 0 2px 10px rgba(0,0,0,0.04); margin-bottom: 20px; }
    .stTabs [data-baseweb="tab"] { height: 44px; padding: 0 20px; background: transparent; border-radius: 10px; font-weight: 600; font-size: 0.95rem; color: #555; border: none; transition: all 0.2s ease; }
    .stTabs [data-baseweb="tab"]:hover { background: #f0f3ff; color: #667eea; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; color: white !important; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.35); }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
    .stTabs [data-baseweb="tab-border"] { display: none; }

    /* Sidebar */
    [data-testid="stSidebar"] { width: 380px !important; background: #ffffff; border-right: 1px solid #e8ecf1; }
    [data-testid="stSidebar"] .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }

    .sb-user-card { display: flex; align-items: center; gap: 12px; padding: 15px; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 12px; color: white; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3); }
    .sb-avatar { font-size: 1.8em; }
    .sb-info h4 { margin: 0; font-size: 1em; font-weight: 700; }
    .sb-info p { margin: 0; font-size: 0.75em; opacity: 0.9; }

    /* Chat Messages */
    [data-testid="stChatMessage"] { padding: 15px 20px; border-radius: 14px; margin-bottom: 12px; border: 1px solid #e8ecf1; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
    [data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) { background: #f7f7f8; margin-left: auto; max-width: 85%; }
    [data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) { background: white; margin-right: auto; max-width: 85%; }
    
    [data-testid="stAudioInput"] { background: linear-gradient(135deg, #f0f3ff 0%, #e7ecff 100%) !important; border-radius: 50% !important; border: 2px solid #667eea !important; padding: 4px !important; transition: all 0.3s ease !important; height: 52px !important; width: 52px !important; min-width: 52px !important; margin-top: 5px !important; }
    [data-testid="stAudioInput"]:hover { border-color: #764ba2 !important; background: linear-gradient(135deg, #e7ecff 0%, #dfe5ff 100%) !important; transform: scale(1.05) !important; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important; }
    
    .stButton > button { border-radius: 10px; font-weight: 600; transition: all 0.2s ease; border: 1px solid #e0e0e0; }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    
    .source-tag { display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 4px 12px; border-radius: 10px; font-size: 0.8em; margin: 3px; font-weight: 500; }
    .success-box { background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); padding: 12px; border-radius: 10px; border-left: 4px solid #28a745; margin: 10px 0; font-size: 0.85em; }
    .voice-info { background: linear-gradient(135deg, #e7f3ff 0%, #d4e9ff 100%); padding: 10px; border-radius: 10px; border-left: 4px solid #0066cc; margin: 8px 0; font-size: 0.9em; color: #0066cc; }
    
    .empty-state { text-align: center; padding: 40px 20px; color: #888; }
    .empty-state .icon { font-size: 4em; margin-bottom: 15px; }
    .empty-state h3 { font-size: 1.3em; color: #333; margin-bottom: 8px; font-weight: 600; }
    .empty-state p { font-size: 0.95em; color: #777; }
    
    .chat-q-box { background: #f7f7f8; padding: 16px 20px; border-radius: 12px; border: 1px solid #e8ecf1; margin: 15px 0 10px 0; font-weight: 500; }
    .chat-a-box { background: white; padding: 20px; border-radius: 12px; border: 1px solid #e8ecf1; margin: 10px 0; line-height: 1.7; white-space: pre-wrap; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
    .loading-dot { display: inline-block; animation: pulse 1s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

    /* Sidebar Chat Box (Messenger Style) */
    .sb-chat-box { display: flex; flex-direction: column; height: 350px; background: #f8f9fa; border-radius: 12px; border: 1px solid #e8ecf1; margin-top: 10px; overflow: hidden; padding: 10px; }
    .sb-msg-bubble { max-width: 85%; padding: 10px 14px; border-radius: 18px; font-size: 0.9em; line-height: 1.4; margin-bottom: 8px; word-wrap: break-word; }
    .sb-msg-user { align-self: flex-end; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-bottom-right-radius: 4px; margin-left: auto; }
    .sb-msg-ai { align-self: flex-start; background: white; color: #333; border: 1px solid #e0e0e0; border-bottom-left-radius: 4px; margin-right: auto; }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    
    @media (max-width: 768px) {
        [data-testid="stSidebar"] { width: 100% !important; }
        .main .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Login Check
# ============================================================
if "user" not in st.session_state: st.session_state.user = None
if st.session_state.user is None:
    from login import login_page
    login_page()
    st.stop()

# ============================================================
# Helper Functions (Chat History & Feedback)
# ============================================================
HISTORY_DIR = "history_data"
os.makedirs(HISTORY_DIR, exist_ok=True)

def get_hist_file(username):
    return os.path.join(HISTORY_DIR, f"{username}.json")

def load_history(username):
    path = get_hist_file(username)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f: 
                return json.load(f)
        except Exception: pass
    return {"chat": {}, "docs": {}, "image": {}, "table": {}}

def save_history(username, data):
    with open(get_hist_file(username), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_to_history(username, category, item_id, title, data_payload, extra_state=None):
    history = load_history(username)
    if category not in history: history[category] = {}
    
    if item_id not in history[category]:
        history[category][item_id] = {
            "title": title[:30] + "..." if len(title) > 30 else title,
            "timestamp": datetime.now().isoformat()
        }
    
    history[category][item_id]["data"] = data_payload
    history[category][item_id]["timestamp"] = datetime.now().isoformat()
    
    if extra_state:
        history[category][item_id]["extra_state"] = extra_state
        
    if len(history[category]) > 20:
        oldest = min(history[category].keys(), key=lambda k: history[category][k]["timestamp"])
        del history[category][oldest]
        
    save_history(username, history)

def delete_history_item(username, category, item_id):
    history = load_history(username)
    if item_id in history.get(category, {}):
        del history[category][item_id]
        save_history(username, history)

FEEDBACK_FILE = "feedback.csv"

def save_feedback(question, answer, rating, username):
    file_exists = os.path.exists(FEEDBACK_FILE)
    try:
        with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists: writer.writerow(["time", "user", "question", "answer", "rating"])
            writer.writerow([datetime.now().isoformat(), username, question[:200], answer[:200], rating])
    except Exception: pass
    try:
        from analytics import log_feedback
        log_feedback(username, question, rating)
    except Exception: pass

# ============================================================
# Other Helper Functions
# ============================================================
def df_to_excel_bytes(df):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Table Data")
    return buffer.getvalue()

def transcribe_audio(audio_path, language="ne-NP"):
    try:
        from voice_input import speech_to_text
        return speech_to_text(audio_path, language=language)
    except Exception as e: return f"Error: {e}"

def generate_tts(text, language="ne"):
    try:
        from voice_output import text_to_speech
        return text_to_speech(text, language=language)
    except Exception: return None

def get_stats():
    stats = {"pdfs": 0, "chunks": 0, "queries": 0}
    if os.path.exists("docs"): stats["pdfs"] = len([f for f in os.listdir("docs") if f.lower().endswith((".pdf", ".xlsx", ".csv"))])
    try:
        import chromadb
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_or_create_collection("docs")
        stats["chunks"] = collection.count()
    except Exception: pass
    stats["queries"] = len(st.session_state.get("messages", [])) // 2
    return stats

def universal_answer(question, context_type="pdf", context_data=None, username="user", target_lang="ne"):
    try:
        from google import genai
        from dotenv import load_dotenv
        load_dotenv()
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        MODEL = "gemini-2.5-flash-lite"
        
        lang_instruction = ""
        if target_lang == "en": lang_instruction = "You must reply strictly in English."
        elif target_lang == "hi": lang_instruction = "आपको केवल हिन्दी में उत्तर देना चाहिए।"
        else: lang_instruction = "तपाईंले अनिवार्य रूपमा नेपालीमा मात्र जवाफ दिनुपर्छ।"
        
        if context_type == "image" and context_data:
            from image_analyzer import detect_mime_type
            from google.genai import types
            with open(context_data, "rb") as f: img_data = f.read()
            mime = detect_mime_type(context_data)
            prompt = f"You are a smart AI.\nAnalyze this image and answer the question.\n\n❓ Question: {question}\n\n⚠️ Rules:\n1. Only use information from the image.\n2. Be careful with text, numbers, names.\n3. Use good format (bold, bullets).\n4. {lang_instruction}\n\nAnswer:"
            response = client.models.generate_content(model=MODEL, contents=[types.Part.from_bytes(data=img_data, mime_type=mime), prompt])
            return response.text
        
        elif context_type == "table" and context_data is not None:
            if isinstance(context_data, pd.DataFrame): table_text = context_data.head(30).to_string(index=False)
            else: table_text = str(context_data)[:3000]
            prompt = f"You are a smart AI.\nAnalyze this table data and answer the question.\n\n📊 Table:\n{table_text}\n\n❓ Question: {question}\n\n⚠️ Rules:\n1. Only use data from the table.\n2. Be careful with numbers.\n3. {lang_instruction}\n\nAnswer:"
            response = client.models.generate_content(model=MODEL, contents=prompt)
            return response.text
        
        elif context_type == "ai_report" and context_data is not None:
            if isinstance(context_data, pd.DataFrame): table_text = context_data.head(30).to_string(index=False)
            else: table_text = str(context_data)[:3000]
            
            if target_lang == "en":
                prompt = f"You are an expert Data Analyst.\nAnalyze this data and create a **Business Report** in **English**.\n\n📊 Data:\n{table_text}\n\n⚠️ Rules:\n1. Write the report in English.\n2. Use Markdown format.\n\nWrite the report like this:\n1. **Executive Summary:** What is the data about and what is the main result?\n2. **Key Findings:** 3-4 points (with Numbers).\n3. **Trends:** What increased or decreased?\n4. **Recommendations:** 2-3 suggestions to improve the business."
            elif target_lang == "hi":
                prompt = f"आप एक विशेषज्ञ डेटा एनालिस्ट हैं।\nइस डेटा का विश्लेषण करके **हिन्दी** में **बिजनेस रिपोर्ट** बनाएं।\n\n📊 डेटा:\n{table_text}\n\n⚠️ नियम:\n1. रिपोर्ट हिन्दी में लिखें।\n2. Markdown फॉर्मेट का उपयोग करें।\n\nरिपोर्ट इस तरह लिखें:\n1. **सारांश (Executive Summary):** डेटा किस बारे में है और मुख्य परिणाम क्या है?\n2. **मुख्य निष्कर्ष (Key Findings):** 3-4 बिंदु (नंबरों के साथ)।\n3. **रुझान (Trends):** क्या बढ़ा या घटा?\n4. **सुझाव (Recommendations):** व्यवसाय सुधारने के लिए 2-3 सुझाव।"
            else:
                prompt = f"तपाईं एक विशेषज्ञ Data Analyst हुनुहुन्छ।\nयो डाटा (Table) लाई विश्लेषण गरेर **नेपालीमा** **Business Report** तयार गर्नुहोस्।\n\n📊 डाटा:\n{table_text}\n\n⚠️ नियमहरू:\n१. रिपोर्ट नेपालीमा लेख्नुहोस्।\n२. Markdown Format प्रयोग गर्नुहोस्।\n\nरिपोर्ट यसरी लेख्नुहोस्:\n१. **सारांश (Executive Summary):** डाटा के बारेमा हो र मुख्य नतिजा के हो?\n२. **मुख्य खोजहरू (Key Findings):** ३-४ वटा बुँदाहरू (Numbers सहित)।\n३. **रुझान (Trends):** के-के बढ्यो वा घट्यो?\n४. **सुझाव (Recommendations):** व्यवसाय सुधार्न २-३ वटा सुझाव।"
            
            response = client.models.generate_content(model=MODEL, contents=prompt)
            return response.text
            
        elif context_type == "pdf":
            try:
                from user_answer import answer_user_question
                from user_manager import get_user_stats
                stats = get_user_stats(username)
                if stats["pdf_count"] > 0:
                    result = answer_user_question(username, question, target_lang=target_lang)
                    return result.get("answer", "❌ जवाफ आएन")
                else:
                    result = answer_question(question, username=username, target_lang=target_lang)
                    return result.get("answer", "❌ जवाफ आएन")
            except Exception as e: return f"❌ {e}"
        
        else:
            prompt = f"Question: {question}\n\n{lang_instruction}\n\nAnswer:"
            response = client.models.generate_content(model=MODEL, contents=prompt)
            return response.text
    except Exception as e: return f"❌ Error: {str(e)[:200]}"

def stream_pdf_answer(question, username="user", target_lang="ne"):
    try:
        from user_vector_store import user_search
        from user_manager import get_user_stats
        from google import genai
        from dotenv import load_dotenv
        load_dotenv()
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        MODEL = "gemini-2.5-flash-lite"
        
        lang_instruction = ""
        if target_lang == "en": lang_instruction = "You must reply strictly in English."
        elif target_lang == "hi": lang_instruction = "आपको केवल हिन्दी में उत्तर देना चाहिए।"
        else: lang_instruction = "तपाईंले अनिवार्य रूपमा नेपालीमा मात्र जवाफ दिनुपर्छ।"
        
        stats = get_user_stats(username)
        if stats["pdf_count"] == 0:
            from vector_store import hybrid_search
            results = hybrid_search(question, n=10, top_n=6)
            docs = [r["text"] for r in results]
            metas = [{"source": r["source"]} for r in results]
        else:
            docs, metas = user_search(username, question, n=6)
        
        if not docs:
            yield "⚠️ No PDF uploaded, or information not found."
            return
        
        context = "\n\n---\n\n".join(docs)
        sources = list(set([m["source"] for m in metas]))
        prompt = f"You are a smart, helpful AI.\nUse the PDF information to answer the question.\n\n📋 Info:\n{context}\n\n❓ Question: {question}\n\n⚠️ Rules:\n1. Answer whatever is asked.\n2. Good format (bold, bullets).\n3. {lang_instruction}\n\nAnswer:"
        
        response = client.models.generate_content_stream(model=MODEL, contents=prompt)
        full_text = ""
        for chunk in response:
            if chunk.text:
                full_text += chunk.text
                yield chunk.text
        if sources:
            yield f"\n\n📚 **Sources:** {' '.join([f'`{s}`' for s in sources])}"
    except Exception as e: yield f"❌ Error: {str(e)[:200]}"

# ============================================================
# Session State
# ============================================================
if "ui_lang" not in st.session_state: st.session_state.ui_lang = "ne"

if "active_chat_id" not in st.session_state: st.session_state.active_chat_id = str(uuid.uuid4())
if "active_doc_id" not in st.session_state: st.session_state.active_doc_id = str(uuid.uuid4())
if "active_img_id" not in st.session_state: st.session_state.active_img_id = str(uuid.uuid4())
if "active_table_id" not in st.session_state: st.session_state.active_table_id = str(uuid.uuid4())

defaults = {
    "messages": [], "voice_text": "", "extracted_tables": None, "extracted_pdf": "", 
    "auto_speak": False, "voice_lang": "ne-NP", "tts_lang": "ne", "last_audio_id": None, 
    "last_docs_audio_id": 0, "last_img_audio_id": 0, "last_table_audio_id": 0, "tag_filter": [], 
    "img_result": "", "img_path_saved": "", "img_name_saved": "", "pending_question": "", 
    "processing": False, "mini_doc_q": "", "mini_doc_a": "", "mini_doc_q_asked": "", 
    "mini_doc_input_version": 0, "mini_img_q": "", "mini_img_a": "", "mini_img_q_asked": "", 
    "mini_img_input_version": 0, "mini_table_q": "", "mini_table_a": "", "mini_table_q_asked": "", 
    "mini_table_input_version": 0, "ai_report_result": "", "feedback_given": set()
}
for key, val in defaults.items():
    if key not in st.session_state: st.session_state[key] = val

lang = st.session_state.ui_lang

# ============================================================
# AI Response Logic for Sidebar Chat
# ============================================================
if st.session_state.get("pending_question"):
    question = st.session_state.pending_question
    st.session_state.processing = True
    
    # User question save
    st.session_state.messages.append({"role": "user", "content": question})
    
    # AI response generate
    full_answer = ""
    try:
        for chunk in stream_pdf_answer(question, st.session_state.user, target_lang=lang):
            full_answer += chunk
    except Exception as e:
        full_answer = f"❌ Error: {e}"
    
    # AI answer save
    st.session_state.messages.append({"role": "assistant", "content": full_answer})
    
    # Save to history
    add_to_history(st.session_state.user, "chat", st.session_state.active_chat_id, question, st.session_state.messages)
    
    st.session_state.pending_question = ""
    st.session_state.processing = False
    st.rerun()

# ============================================================
# SIDEBAR (Ultimate Messenger Style)
# ============================================================
with st.sidebar:
    # User Info
    st.markdown(f"""
    <div class="sb-user-card">
        <div class="sb-avatar">👤</div>
        <div class="sb-info">
            <h4>{st.session_state.user}</h4>
            <p>{st.session_state.get("user_role", "user").upper()}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # New Chat Button
    if st.button(t("chat_clear", lang), use_container_width=True, type="primary", key="sidebar_new_chat"):
        st.session_state.active_chat_id = str(uuid.uuid4())
        st.session_state.active_doc_id = str(uuid.uuid4())
        st.session_state.active_img_id = str(uuid.uuid4())
        st.session_state.active_table_id = str(uuid.uuid4())
        
        st.session_state.messages = []
        st.session_state.pending_question = ""
        st.session_state.extracted_tables = None
        st.session_state.extracted_pdf = ""
        st.session_state.img_path_saved = ""
        st.session_state.img_name_saved = ""
        st.session_state.img_result = ""
        st.session_state.ai_report_result = ""
        st.session_state.mini_doc_q = ""
        st.session_state.mini_doc_a = ""
        st.session_state.mini_img_q = ""
        st.session_state.mini_img_a = ""
        st.session_state.mini_table_q = ""
        st.session_state.mini_table_a = ""
        st.rerun()

    user_history = load_history(st.session_state.user)

    # ⚠️ 1. Sidebar Chat List (Messenger Style)
    st.markdown(f"**{t('chat_history', lang)}**")
    if user_history.get("chat"):
        for cid, cdata in sorted(user_history["chat"].items(), key=lambda x: x[1]["timestamp"], reverse=True)[:5]:
            is_active = st.session_state.active_chat_id == cid
            if st.button(f"👤 {cdata['title']}", key=f"sb_chat_{cid}", use_container_width=True, type="secondary" if not is_active else "primary"):
                st.session_state.active_chat_id = cid
                st.session_state.messages = cdata["data"]
                st.rerun()
    else: 
        st.caption(t("no_history", lang))

    # ⚠️ 2. Sidebar Chat Box
    st.markdown("---")
    st.markdown(f"#### 🧠 PDF Brain AI")
    
    # Chat Messages Container
    chat_container = st.container(height=300)
    with chat_container:
        if not st.session_state.messages:
            st.caption(t("chat_welcome", lang))
        else:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(f'<div class="sb-msg-bubble sb-msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="sb-msg-bubble sb-msg-ai">{msg["content"]}</div>', unsafe_allow_html=True)
            
        if st.session_state.get("processing"):
            st.markdown(f'<div class="sb-msg-bubble sb-msg-ai">▌ {t("thinking", lang)}</div>', unsafe_allow_html=True)

    # Chat Input inside Sidebar
    prompt = st.chat_input(t("chat_input", lang), key="sidebar_chat_input")
    if prompt:
        st.session_state.pending_question = prompt
        st.rerun()

    st.markdown("---")

    # ⚠️ 3. Documents History
    with st.expander(f"📄 {t('doc_history', lang)}"):
        if user_history.get("docs"):
            for did, ddata in sorted(user_history["docs"].items(), key=lambda x: x[1]["timestamp"], reverse=True)[:3]:
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 10px; padding: 8px; border-radius: 8px; margin-bottom: 5px;">
                    <div style="font-size: 1.2em;">📄</div>
                    <div style="flex-grow: 1; overflow: hidden;">
                        <div style="font-size: 0.85em; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{ddata['title']}</div>
                        <div style="font-size: 0.7em; color: #888;">{ddata['timestamp'][:10]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button("Open Doc Q&A", key=f"dc_{did}", use_container_width=True):
                        st.session_state.active_doc_id = did
                        st.session_state.mini_doc_q = ddata.get("extra_state", {}).get("q", "")
                        st.session_state.mini_doc_a = ddata["data"]
                        st.session_state.mini_doc_q_asked = ddata.get("extra_state", {}).get("q", "")
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"ddc_{did}"):
                        delete_history_item(st.session_state.user, "docs", did)
                        st.rerun()
        else: st.caption(t("no_history", lang))

    # ⚠️ 4. Image History
    with st.expander(f"🖼️ {t('img_history', lang)}"):
        if user_history.get("image"):
            for iid, idata in sorted(user_history["image"].items(), key=lambda x: x[1]["timestamp"], reverse=True)[:3]:
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 10px; padding: 8px; border-radius: 8px; margin-bottom: 5px;">
                    <div style="font-size: 1.2em;">🖼️</div>
                    <div style="flex-grow: 1; overflow: hidden;">
                        <div style="font-size: 0.85em; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{idata['title']}</div>
                        <div style="font-size: 0.7em; color: #888;">{idata['timestamp'][:10]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button("Open Image Q&A", key=f"im_{iid}", use_container_width=True):
                        st.session_state.active_img_id = iid
                        st.session_state.img_path_saved = idata.get("extra_state", {}).get("path", "")
                        st.session_state.img_name_saved = idata.get("extra_state", {}).get("name", "")
                        st.session_state.mini_img_q = idata.get("extra_state", {}).get("q", "")
                        st.session_state.mini_img_a = idata["data"]
                        st.session_state.mini_img_q_asked = idata.get("extra_state", {}).get("q", "")
                        st.session_state.img_result = idata.get("extra_state", {}).get("result", "")
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"dim_{iid}"):
                        delete_history_item(st.session_state.user, "image", iid)
                        st.rerun()
        else: st.caption(t("no_history", lang))

    # ⚠️ 5. Table History
    with st.expander(f"📊 {t('table_history', lang)}"):
        if user_history.get("table"):
            for tid, tdata in sorted(user_history["table"].items(), key=lambda x: x[1]["timestamp"], reverse=True)[:3]:
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 10px; padding: 8px; border-radius: 8px; margin-bottom: 5px;">
                    <div style="font-size: 1.2em;">📊</div>
                    <div style="flex-grow: 1; overflow: hidden;">
                        <div style="font-size: 0.85em; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{tdata['title']}</div>
                        <div style="font-size: 0.7em; color: #888;">{tdata['timestamp'][:10]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button("Open Table Q&A", key=f"tb_{tid}", use_container_width=True):
                        st.session_state.active_table_id = tid
                        st.session_state.extracted_pdf = tdata.get("extra_state", {}).get("pdf", "")
                        st.session_state.mini_table_q = tdata.get("extra_state", {}).get("q", "")
                        st.session_state.mini_table_a = tdata["data"]
                        st.session_state.mini_table_q_asked = tdata.get("extra_state", {}).get("q", "")
                        if tdata.get("extra_state", {}).get("tables"):
                            restored = []
                            for t in tdata["extra_state"]["tables"]:
                                restored.append({
                                    "page": t["page"], "index": t["index"], "rows": t["rows"], "cols": t["cols"],
                                    "dataframe": pd.DataFrame(t["dataframe"])
                                })
                            st.session_state.extracted_tables = restored
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"dtb_{tid}"):
                        delete_history_item(st.session_state.user, "table", tid)
                        st.rerun()
        else: st.caption(t("no_history", lang))

    st.markdown("---")
    st.markdown(f"**🌐 {t('ui_language', lang)}**")
    ui_lang_map = {"🇳🇵 नेपाली": "ne", "🇬🇧 English": "en", "🇮🇳 हिन्दी": "hi"}
    ui_keys = list(ui_lang_map.keys()); ui_values = list(ui_lang_map.values())
    current_index = ui_values.index(lang) if lang in ui_values else 0
    selected_ui = st.selectbox(t("ui_language", lang), ui_keys, index=current_index, key="ui_lang_select", label_visibility="collapsed")
    new_lang = ui_lang_map[selected_ui]
    if new_lang != lang: st.session_state.ui_lang = new_lang; st.rerun()
    
    with st.expander(f"🎤 {t('voice_settings', lang)}"):
        st.session_state.auto_speak = st.toggle(t("auto_speak", lang), value=st.session_state.auto_speak)
        voice_lang_map = {"नेपाली": "ne-NP", "English": "en-US", "हिन्दी": "hi-IN"}
        voice_label = st.selectbox(t("input_lang", lang), list(voice_lang_map.keys()), index=0, key="v_lang_in")
        st.session_state.voice_lang = voice_lang_map[voice_label]
        tts_lang_map = {"नेपाली": "ne", "English": "en", "हिन्दी": "hi"}
        tts_label = st.selectbox(t("output_lang", lang), list(tts_lang_map.keys()), index=0, key="v_lang_out")
        st.session_state.tts_lang = tts_lang_map[tts_label]
    
    if st.button(t("logout", lang), use_container_width=True, key="sidebar_logout"):
        st.session_state.user = None; st.session_state.messages = []
        st.session_state.chat_loaded = False; st.rerun()
    
    st.markdown("---")
    st.caption("🧠 **PDF Brain** v26.0")

# ============================================================
# MAIN AREA (Tabs) - Chat Tab Removed
# ============================================================
render_sticky_header(st.session_state.user, lang)

# ⚠️ Chat Tab (tab1) removed. Now only 3 tabs.
tab1, tab2, tab3 = st.tabs([t("docs_tab", lang), t("image_tab", lang), t("table_tab", lang)])

# ============================================================
# TAB 1: DOCUMENTS (Previously Tab 2)
# ============================================================
with tab1:
    st.markdown(f"### {t('my_docs', lang)}")
    try:
        from user_manager import list_user_pdfs, save_user_pdf, delete_user_pdf, get_user_stats
        user_stats = get_user_stats(st.session_state.user)
        col1, col2, col3 = st.columns(3)
        col1.metric("📄 Files", user_stats['pdf_count']); col2.metric("✂️ Chunks", user_stats['chunks']); col3.metric("💾 Size", f"{user_stats['total_size']/1024:.1f} KB")
        
        st.markdown("---")
        st.markdown(f"#### {t('upload_doc', lang)}")
        st.caption(t("upload_hint", lang))
        uploaded_files = st.file_uploader(t("upload_doc", lang), type=["pdf", "docx", "doc", "txt", "md", "jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key="user_doc_upload", label_visibility="collapsed")
        
        if uploaded_files:
            if st.button(t("upload_process", lang), use_container_width=True, type="primary", key="docs_upload_process"):
                uploaded_count = 0
                with st.spinner(t("uploading", lang)):
                    for file in uploaded_files:
                        try:
                            save_user_pdf(st.session_state.user, file.getbuffer(), file.name); uploaded_count += 1
                        except Exception as e: st.error(f"❌ {file.name}: {e}")
                if uploaded_count > 0:
                    st.success(f"✅ {uploaded_count} {t('files_saved', lang)}")
                    with st.spinner(t("processing", lang)):
                        try:
                            from user_vector_store import build_user_database
                            build_user_database(st.session_state.user, reset=True); st.success(f"✅ {t('ai_ready', lang)}")
                        except Exception as e: st.error(f"❌ {e}")
                    time.sleep(1); st.rerun()
        
        st.markdown("---")
        user_files = list_user_pdfs(st.session_state.user)
        if user_files:
            st.markdown(f"#### {t('my_files', lang)} ({len(user_files)})")
            for doc in user_files:
                col1, col2, col3 = st.columns([4, 2, 1])
                with col1: st.markdown(f"{doc.get('icon', '📄')} **{doc['name']}**")
                with col2: st.caption(f"{doc.get('format', 'FILE')} • {doc['size']/1024:.1f} KB")
                with col3:
                    if st.button("🗑️", key=f"del_file_{doc['name']}"):
                        if delete_user_pdf(st.session_state.user, doc["name"]):
                            try:
                                from user_vector_store import build_user_database
                                build_user_database(st.session_state.user, reset=True)
                            except Exception: pass
                            st.success(t("deleted", lang)); st.rerun()
            
            st.markdown("---")
            st.markdown(f"#### {t('ask_docs', lang)}")
            st.caption(t("ask_hint", lang))
            
            input_key_docs = f"mini_doc_input_{st.session_state.get('mini_doc_input_version', 0)}"
            col_voice_docs, col_input_docs = st.columns([1, 8])
            
            with col_voice_docs:
                docs_audio = st.audio_input("🎤", key="docs_voice_recorder", label_visibility="collapsed")
                if docs_audio is not None:
                    docs_audio_id = hash(docs_audio.getvalue())
                    if docs_audio_id != st.session_state.get("last_docs_audio_id", 0):
                        st.session_state.last_docs_audio_id = docs_audio_id
                        with st.spinner("🎤 सुन्दै..."):
                            os.makedirs("temp_audio", exist_ok=True)
                            audio_path = os.path.join("temp_audio", "docs_voice.wav")
                            with open(audio_path, "wb") as f: f.write(docs_audio.getbuffer())
                            text = transcribe_audio(audio_path, st.session_state.voice_lang)
                            if text and not text.startswith("Error") and len(text.strip()) > 2:
                                st.session_state.mini_doc_q = text; st.rerun()
            
            with col_input_docs:
                mini_doc_q = st.text_input(t("your_question", lang), value="", placeholder=t("ask_placeholder", lang), key=input_key_docs, label_visibility="collapsed")
            
            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                ask_clicked = st.button(t("ask_btn", lang), key="docs_ask_btn", use_container_width=True, type="primary")
            with col_btn2:
                if st.button(t("clear_btn", lang), key="docs_clear_btn", use_container_width=True):
                    st.session_state.mini_doc_q = ""; st.session_state.mini_doc_a = ""
                    st.session_state.mini_doc_input_version += 1; st.rerun()
            
            if (ask_clicked or mini_doc_q) and mini_doc_q.strip():
                st.session_state.mini_doc_q_asked = mini_doc_q
                st.markdown(f'<div class="chat-q-box">👤 <b>{t("your_question", lang)}:</b><br>{mini_doc_q}</div>', unsafe_allow_html=True)
                st.markdown(f"🧠 **{t('ai_answer', lang)}:**")
                
                answer_placeholder = st.empty(); full_answer = ""
                try:
                    for chunk in stream_pdf_answer(mini_doc_q, st.session_state.user, target_lang=lang):
                        full_answer += chunk
                        answer_placeholder.markdown(f'<div class="chat-a-box">{full_answer}<span class="loading-dot">▌</span></div>', unsafe_allow_html=True)
                    answer_placeholder.markdown(f'<div class="chat-a-box">{full_answer}</div>', unsafe_allow_html=True)
                    
                    st.session_state.mini_doc_a = full_answer
                    add_to_history(st.session_state.user, "docs", st.session_state.active_doc_id, mini_doc_q, full_answer, {"q": mini_doc_q})
                    
                    st.session_state.mini_doc_input_version += 1
                    st.rerun()
                except Exception as e: st.error(f"❌ {e}")
            
            elif st.session_state.get("mini_doc_a"):
                st.markdown(f'<div class="chat-q-box">👤 <b>{t("your_question", lang)}:</b><br>{st.session_state.get("mini_doc_q_asked", "")}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="chat-a-box">🧠 {st.session_state.mini_doc_a}</div>', unsafe_allow_html=True)
                if st.button(t("copy_answer", lang), key="copy_doc_ans"): st.code(st.session_state.mini_doc_a, language=None)
        else: st.info(t("no_files", lang))
    except ImportError: st.error("⚠️ user_manager.py भेटिएन")

# ============================================================
# TAB 2: IMAGE (Previously Tab 3)
# ============================================================
with tab2:
    st.markdown(f"### {t('image_analysis', lang)}")
    st.caption(t("image_hint", lang))
    col1, col2 = st.columns([1, 1])
    with col1:
        uploaded_image = st.file_uploader(t("upload_image", lang), type=["jpg", "jpeg", "png", "webp"], key="img_upload_tab", label_visibility="collapsed")
        if uploaded_image:
            os.makedirs("temp_images", exist_ok=True)
            img_path = os.path.join("temp_images", uploaded_image.name)
            with open(img_path, "wb") as f: f.write(uploaded_image.getbuffer())
            st.session_state.img_path_saved = img_path; st.session_state.img_name_saved = uploaded_image.name
        
        if st.session_state.get("img_path_saved") and os.path.exists(st.session_state.img_path_saved):
            st.image(st.session_state.img_path_saved, caption=st.session_state.get("img_name_saved", ""), width="stretch")
            mode = st.selectbox(t("analysis_type", lang), ["🔍 Auto", "📝 Text", "📊 Table", "🔢 Numbers", "🌐 Describe", "❓ Question"], key="img_mode_tab")
            img_question = ""
            if "Question" in mode or "प्रश्न" in mode:
                img_question = st.text_input(t("your_question", lang), placeholder=t("image_placeholder", lang), key="img_q_tab")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button(t("analyze_btn", lang), use_container_width=True, type="primary", key="img_analyze_btn"):
                    with st.spinner(t("analyzing", lang)):
                        try:
                            from image_analyzer import analyze_image, extract_numbers_from_image
                            img_path = st.session_state.img_path_saved
                            if mode == "🔍 Auto": result = analyze_image(img_path)
                            elif mode == "📝 Text": result = analyze_image(img_path, mode="text")
                            elif mode == "📊 Table": result = analyze_image(img_path, mode="extract_table")
                            elif mode == "🔢 Numbers": result = extract_numbers_from_image(img_path)
                            elif mode == "🌐 Describe": result = analyze_image(img_path, mode="describe")
                            elif "Question" in mode or "प्रश्न" in mode: result = analyze_image(img_path, question=img_question) if img_question else "❌"
                            else: result = analyze_image(img_path)
                            st.session_state.img_result = result
                        except Exception as e: st.session_state.img_result = f"❌ {e}"
            with col_btn2:
                if st.button(t("delete_btn", lang), use_container_width=True, key="img_delete_btn"):
                    if os.path.exists(st.session_state.img_path_saved):
                        try: os.remove(st.session_state.img_path_saved)
                        except Exception: pass
                    st.session_state.img_path_saved = ""; st.session_state.img_name_saved = ""; st.session_state.img_result = ""; st.session_state.mini_img_a = ""; st.rerun()
        else: st.info(t("upload_prompt", lang))
    
    with col2:
        st.markdown(f"#### {t('result', lang)}")
        if st.session_state.get("img_result"): st.markdown(st.session_state.img_result)
        else: st.markdown(f'<div class="empty-state"><div class="icon">🖼️</div><p>{t("upload_prompt", lang)}</p></div>', unsafe_allow_html=True)
    
    if st.session_state.get("img_path_saved") and os.path.exists(st.session_state.img_path_saved):
        st.markdown("---")
        st.markdown(f"#### {t('image_question', lang)}")
        st.caption(t("ask_hint", lang))
        
        input_key_img = f"mini_img_input_{st.session_state.get('mini_img_input_version', 0)}"
        col_voice_img, col_input_img = st.columns([1, 8])
        
        with col_voice_img:
            img_audio = st.audio_input("🎤", key="img_voice_recorder", label_visibility="collapsed")
            if img_audio is not None:
                img_audio_id = hash(img_audio.getvalue())
                if img_audio_id != st.session_state.get("last_img_audio_id", 0):
                    st.session_state.last_img_audio_id = img_audio_id
                    with st.spinner("🎤 सुन्दै..."):
                        os.makedirs("temp_audio", exist_ok=True)
                        audio_path = os.path.join("temp_audio", "img_voice.wav")
                        with open(audio_path, "wb") as f: f.write(img_audio.getbuffer())
                        text = transcribe_audio(audio_path, st.session_state.voice_lang)
                        if text and not text.startswith("Error") and len(text.strip()) > 2:
                            st.session_state.mini_img_q = text; st.rerun()
        
        with col_input_img:
            mini_img_q = st.text_input(t("your_question", lang), value="", placeholder=t("image_placeholder", lang), key=input_key_img, label_visibility="collapsed")
        
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            img_ask_clicked = st.button(t("ask_btn", lang), key="img_ask_btn", use_container_width=True, type="primary")
        with col_btn2:
            if st.button(t("clear_btn", lang), key="img_clear_btn", use_container_width=True):
                st.session_state.mini_img_q = ""; st.session_state.mini_img_a = ""
                st.session_state.mini_img_input_version += 1; st.rerun()
        
        if (img_ask_clicked or mini_img_q) and mini_img_q.strip():
            st.session_state.mini_img_q_asked = mini_img_q
            st.markdown(f'<div class="chat-q-box">👤 <b>{t("your_question", lang)}:</b><br>{mini_img_q}</div>', unsafe_allow_html=True)
            st.markdown(f"🧠 **{t('ai_answer', lang)}:**")
            with st.spinner(t("analyzing", lang)):
                answer = universal_answer(mini_img_q, context_type="image", context_data=st.session_state.img_path_saved, target_lang=lang)
                st.session_state.mini_img_a = answer
            st.markdown(f'<div class="chat-a-box">{answer}</div>', unsafe_allow_html=True)
            
            add_to_history(st.session_state.user, "image", st.session_state.active_img_id, st.session_state.img_name_saved, answer, 
                           {"path": st.session_state.img_path_saved, "name": st.session_state.img_name_saved, "q": mini_img_q, "result": st.session_state.img_result})
            
            st.session_state.mini_img_input_version += 1
            st.rerun()
        
        elif st.session_state.get("mini_img_a"):
            st.markdown(f'<div class="chat-q-box">👤 <b>{t("your_question", lang)}:</b><br>{st.session_state.get("mini_img_q_asked", "")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-a-box">🧠 {st.session_state.mini_img_a}</div>', unsafe_allow_html=True)
            if st.button(t("copy_answer", lang), key="copy_img_ans"): st.code(st.session_state.mini_img_a, language=None)

# ============================================================
# TAB 3: TABLE + CHART (Previously Tab 4)
# ============================================================
with tab3:
    st.markdown(f"### {t('table_chart', lang)}")
    st.caption(t("table_hint", lang))
    
    source_option = st.radio(
        t("where_extract", lang),
        [t("upload_new_file", lang), t("select_from_docs", lang)],
        horizontal=True, label_visibility="collapsed"
    )
    
    tables = None
    file_display_name = ""
    
    if source_option == t("upload_new_file", lang):
        uploaded_table_file = st.file_uploader(
            t("upload_file_label", lang),
            type=["pdf", "xlsx", "xls", "csv", "jpg", "jpeg", "png"],
            key="table_file_uploader"
        )
        
        if uploaded_table_file:
            if st.button(t("extract_tables_btn", lang), use_container_width=True, type="primary", key="extract_from_upload"):
                with st.spinner(t("extracting", lang)):
                    try:
                        os.makedirs("temp_tables", exist_ok=True)
                        temp_path = os.path.join("temp_tables", uploaded_table_file.name)
                        with open(temp_path, "wb") as f: f.write(uploaded_table_file.getbuffer())
                        
                        file_ext = uploaded_table_file.name.lower().split(".")[-1]
                        file_display_name = uploaded_table_file.name
                        
                        if file_ext == "pdf":
                            from table_extractor import extract_tables
                            tables = extract_tables(temp_path)
                        elif file_ext in ["xlsx", "xls"]:
                            xls = pd.ExcelFile(temp_path)
                            tables = []
                            for sheet_name in xls.sheet_names:
                                df = pd.read_excel(xls, sheet_name=sheet_name)
                                tables.append({"page": 1, "index": sheet_name, "dataframe": df, "rows": len(df), "cols": len(df.columns)})
                        elif file_ext == "csv":
                            df = pd.read_csv(temp_path)
                            tables = [{"page": 1, "index": 1, "dataframe": df, "rows": len(df), "cols": len(df.columns)}]
                        elif file_ext in ["jpg", "jpeg", "png"]:
                            from image_analyzer import analyze_image
                            result_text = analyze_image(temp_path, question="Extract all data from this table. Return ONLY a valid CSV format. No explanation, no markdown code blocks, just plain CSV text with headers.")
                            st.info(t("image_table_msg", lang))
                            
                            try:
                                clean_csv = result_text.replace("```csv", "").replace("```", "").strip()
                                from io import StringIO
                                image_df = pd.read_csv(StringIO(clean_csv), sep=None, engine='python')
                                st.dataframe(image_df, use_container_width=True)
                                st.download_button(
                                    label=t("download_img_excel", lang),
                                    data=df_to_excel_bytes(image_df),
                                    file_name="image_extracted_table.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key="dl_img_excel"
                                )
                            except Exception:
                                st.warning(t("ai_parse_error", lang))
                                st.text(result_text)
                            
                        if tables:
                            st.session_state.extracted_tables = tables
                            st.session_state.extracted_pdf = file_display_name
                            add_to_history(st.session_state.user, "table", st.session_state.active_table_id, file_display_name, "Extracted", 
                                           {"pdf": file_display_name, "tables": [{"page": t["page"], "index": t["index"], "rows": t["rows"], "cols": t["cols"], "dataframe": t["dataframe"].to_dict(orient="records")} for t in tables]})
                            st.rerun()
                        elif file_ext not in ["jpg", "jpeg", "png"]:
                            st.warning(t("no_table", lang))
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    else:
        if os.path.exists("docs"):
            pdf_files = [f for f in os.listdir("docs") if f.lower().endswith((".pdf", ".xlsx", ".csv"))]
            if pdf_files:
                col1, col2 = st.columns([3, 1])
                with col1:
                    selected_pdf = st.selectbox(t("pdf_select", lang), pdf_files, key="table_pdf_tab")
                with col2:
                    st.write("")
                    if st.button(t("analyze_btn", lang), use_container_width=True, type="primary", key="table_analyze_btn"):
                        with st.spinner(t("extracting", lang)):
                            try:
                                file_path = os.path.join("docs", selected_pdf)
                                file_ext = selected_pdf.lower().split(".")[-1]
                                file_display_name = selected_pdf
                                
                                if file_ext == "pdf":
                                    from table_extractor import extract_tables
                                    tables = extract_tables(file_path)
                                elif file_ext in ["xlsx", "xls"]:
                                    xls = pd.ExcelFile(file_path)
                                    tables = []
                                    for sheet_name in xls.sheet_names:
                                        df = pd.read_excel(xls, sheet_name=sheet_name)
                                        tables.append({"page": 1, "index": sheet_name, "dataframe": df, "rows": len(df), "cols": len(df.columns)})
                                elif file_ext == "csv":
                                    df = pd.read_csv(file_path)
                                    tables = [{"page": 1, "index": 1, "dataframe": df, "rows": len(df), "cols": len(df.columns)}]
                                
                                if tables:
                                    st.session_state.extracted_tables = tables
                                    st.session_state.extracted_pdf = file_display_name
                                    add_to_history(st.session_state.user, "table", st.session_state.active_table_id, file_display_name, "Extracted", 
                                                   {"pdf": file_display_name, "tables": [{"page": t["page"], "index": t["index"], "rows": t["rows"], "cols": t["cols"], "dataframe": t["dataframe"].to_dict(orient="records")} for t in tables]})
                                    st.rerun()
                                else:
                                    st.warning(t("no_table", lang))
                            except Exception as e:
                                st.error(f"❌ {e}")
            else:
                st.info(t("no_pdf", lang))
        else:
            st.info(t("no_docs_folder", lang))

    # ============================================================
    # नतिजा देखाउने
    # ============================================================
    if st.session_state.get("extracted_tables"):
        tables = st.session_state.extracted_tables
        st.success(f"✅ {len(tables)} {t('table_found_msg', lang)} {st.session_state.extracted_pdf}")
        
        from chart_maker import make_chart, get_summary_stats, df_to_csv_bytes
        
        for idx, tbl in enumerate(tables, 1):
            df = tbl["dataframe"].copy()
            
            with st.expander(
                f"📋 Table {idx} — Page/Sheet {tbl['page']} ({tbl['rows']}×{tbl['cols']})",
                expanded=(idx == 1)
            ):
                sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
                    t("data_tab", lang), t("chart_tab", lang), t("stats_tab", lang), "🤖 AI Report"
                ])
                
                with sub_tab1:
                    st.dataframe(df, use_container_width=True)
                    
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            t("download_excel", lang), 
                            df_to_excel_bytes(df),
                            file_name=f"table_{idx}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"xlsx_{idx}",
                            use_container_width=True
                        )
                    with col_dl2:
                        st.download_button(
                            t("download_csv", lang), 
                            df_to_csv_bytes(df),
                            file_name=f"table_{idx}.csv",
                            mime="text/csv",
                            key=f"csv_{idx}",
                            use_container_width=True
                        )
                
                with sub_tab2:
                    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
                    if not numeric_cols:
                        for col in df.columns:
                            df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[$,]', '', regex=True), errors="coerce")
                        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
                    
                    if numeric_cols:
                        text_cols = [c for c in df.columns if c not in numeric_cols]
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            x_default = text_cols[0] if text_cols else df.columns[0]
                            x_index = df.columns.tolist().index(x_default) if x_default in df.columns.tolist() else 0
                            x_col = st.selectbox("X", df.columns.tolist(), index=x_index, key=f"tab_x_{idx}")
                        with c2:
                            y_col = st.selectbox("Y", numeric_cols, key=f"tab_y_{idx}")
                        with c3:
                            chart_type = st.selectbox("Type", ["bar", "line", "pie", "area", "scatter"], key=f"tab_t_{idx}")
                        
                        fig = make_chart(df, chart_type=chart_type, x_col=x_col, y_col=y_col)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning(t("no_numeric", lang))
                
                with sub_tab3:
                    stats = get_summary_stats(df)
                    for col, s in stats.items():
                        st.markdown(f"**📊 {col}**")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric(t("sum", lang), f"{s['sum']:,.2f}")
                        c2.metric(t("avg", lang), f"{s['mean']:,.2f}")
                        c3.metric(t("min", lang), f"{s['min']:,.2f}")
                        c4.metric(t("max", lang), f"{s['max']:,.2f}")
                
                with sub_tab4:
                    st.markdown(f"#### {t('ai_report_title', lang)}")
                    st.caption(t("ai_report_desc", lang))
                    
                    if st.button(t("ai_report_btn", lang), key=f"ai_report_{idx}", use_container_width=True, type="primary"):
                        with st.spinner("AI..."):
                            report = universal_answer("", context_type="ai_report", context_data=df, target_lang=lang)
                            st.session_state.ai_report_result = report
                    
                    if st.session_state.get("ai_report_result"):
                        st.markdown(f'<div class="chat-a-box">{st.session_state.ai_report_result}</div>', unsafe_allow_html=True)
                        st.download_button(
                            t("download_report", lang),
                            st.session_state.ai_report_result,
                            file_name=f"AI_Report_{idx}.txt",
                            mime="text/plain",
                            key=f"dl_report_{idx}"
                        )
        
        st.markdown("---")
        st.markdown(f"#### {t('table_question', lang)}")
        st.caption(t("ask_hint", lang))
        
        input_key_table = f"mini_table_input_{st.session_state.get('mini_table_input_version', 0)}"
        col_voice_table, col_input_table = st.columns([1, 8])
        
        with col_voice_table:
            table_audio = st.audio_input("🎤", key="table_voice_recorder", label_visibility="collapsed")
            if table_audio is not None:
                table_audio_id = hash(table_audio.getvalue())
                if table_audio_id != st.session_state.get("last_table_audio_id", 0):
                    st.session_state.last_table_audio_id = table_audio_id
                    with st.spinner("🎤 सुन्दै..."):
                        os.makedirs("temp_audio", exist_ok=True)
                        audio_path = os.path.join("temp_audio", "table_voice.wav")
                        with open(audio_path, "wb") as f: f.write(table_audio.getbuffer())
                        text = transcribe_audio(audio_path, st.session_state.voice_lang)
                        if text and not text.startswith("Error") and len(text.strip()) > 2:
                            st.session_state.mini_table_q = text
                            st.rerun()
        
        with col_input_table:
            mini_table_q = st.text_input(
                t("your_question", lang),
                value="",
                placeholder=t("table_placeholder", lang),
                key=input_key_table,
                label_visibility="collapsed"
            )
        
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            table_ask_clicked = st.button(t("ask_btn", lang), key="table_ask_btn", use_container_width=True, type="primary")
        with col_btn2:
            if st.button(t("clear_btn", lang), key="table_clear_btn", use_container_width=True):
                st.session_state.mini_table_q = ""
                st.session_state.mini_table_a = ""
                st.session_state.mini_table_input_version += 1
                st.rerun()
        
        if (table_ask_clicked or mini_table_q) and mini_table_q.strip():
            st.session_state.mini_table_q_asked = mini_table_q
            st.markdown(f'<div class="chat-q-box">👤 <b>{t("your_question", lang)}:</b><br>{mini_table_q}</div>', unsafe_allow_html=True)
            
            with st.spinner(t("thinking", lang)):
                tables_data = [tbl["dataframe"].head(20).to_string(index=False) for tbl in tables]
                combined = "\n\n---\n\n".join(tables_data)
                answer = universal_answer(mini_table_q, context_type="table", context_data=combined, target_lang=lang)
                st.session_state.mini_table_a = answer
            
            st.markdown(f'<div class="chat-a-box">🧠 {answer}</div>', unsafe_allow_html=True)
            
            add_to_history(st.session_state.user, "table", st.session_state.active_table_id, st.session_state.extracted_pdf, answer, 
                           {"pdf": st.session_state.extracted_pdf, "q": mini_table_q, "tables": [{"page": t["page"], "index": t["index"], "rows": t["rows"], "cols": t["cols"], "dataframe": t["dataframe"].to_dict(orient="records")} for t in tables]})
            
            st.session_state.mini_table_input_version += 1
            st.rerun()
        
        elif st.session_state.get("mini_table_a"):
            st.markdown(f'<div class="chat-q-box">👤 <b>{t("your_question", lang)}:</b><br>{st.session_state.get("mini_table_q_asked", "")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-a-box">🧠 {st.session_state.mini_table_a}</div>', unsafe_allow_html=True)
            if st.button(t("copy_answer", lang), key="copy_table_ans"):
                st.code(st.session_state.mini_table_a, language=None)

# ============================================================
# FOOTER
# ============================================================
stats_final = get_stats()
st.markdown("---")
fcol1, fcol2, fcol3 = st.columns(3)
with fcol1:
    st.markdown("#### 🧠 PDF Brain")
    st.caption(f"**Version:** 26.0 Pro")
    st.caption(f"**User:** {st.session_state.user}")
with fcol2:
    st.markdown(f"#### 📊 {t('queries', lang).title()}")
    st.caption(f"💬 {stats_final['queries']} {t('queries', lang)}")
    st.caption(f"📄 {stats_final['pdfs']} PDFs")
with fcol3:
    st.markdown(f"#### ⚙️ Status")
    st.caption(f"✂️ {stats_final['chunks']} chunks")
    st.caption(f"🌐 {lang.upper()}")
st.markdown("---")
st.caption(f"**{t('made_with', lang)}** | © 2026 PDF Brain | Powered by Gemini AI")