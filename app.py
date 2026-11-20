# app.py — PDF Brain v52.0 (Final Full Code with Messenger Fix)
import os
import csv
import io
import json
import time
import uuid
import base64
import sqlite3
import re
import sys
from datetime import datetime
import pandas as pd
import streamlit as st
import base64
from PIL import Image
from answer import answer_question
from sticky_header import render_sticky_header
from google import genai
from google.genai import types
from dotenv import load_dotenv
from email_server import send_email_with_attachment
from pathlib import Path
from caption_maker import generate_srt, load_whisper_model
from caption_translator import translate_srt_gemini
from subtitle_tools import burn_subtitles, parse_srt, save_srt
from client_manager import add_client, get_clients, add_project, get_projects, update_project_status
from file_delivery import create_delivery_link, get_delivery_file

from google_sync import (
    get_google_services, create_spreadsheet, write_dataframe_to_sheet,
    read_sheet_as_dataframe, upload_file_to_drive, list_drive_files,
    download_file_from_drive
)

from memory_system import (
    save_memory, get_memories, get_memory_context,
    extract_memories_from_text, summarize_conversation,
    get_latest_summary, delete_memory, clear_all_memories
)
from video_converter import (
    get_ffmpeg_path,
    get_video_info,
    convert_to_hd,
    quick_hd_convert,
    compress_video,
    apply_hd_effect,
    apply_hd_filter,
    change_voice_pitch,
    extract_audio,
    convert_with_effect,
)
from security import log_action, get_audit_logs
from video_editor import trim_video, add_text, add_music, apply_filter, apply_effect, merge_videos
from admin import render_admin_panel

load_dotenv()

# ============================================================
# 🎨 AVATAR HELPER FUNCTIONS
# ============================================================
AVATAR_DIR = "avatar_uploads"
os.makedirs(AVATAR_DIR, exist_ok=True)

def get_avatar_path(username):
    """प्रयोगकर्ताको avatar फाइल खोज्ने"""
    for ext in ["png", "jpg", "jpeg", "webp"]:
        path = os.path.join(AVATAR_DIR, f"{username}.{ext}")
        if os.path.exists(path):
            return path
    return None

def save_avatar(username, uploaded_file):
    """Avatar सेभ गर्ने"""
    # पुरानो हटाउने
    old = get_avatar_path(username)
    if old:
        os.remove(old)
    # नयाँ सेभ
    ext = uploaded_file.name.split(".")[-1].lower()
    path = os.path.join(AVATAR_DIR, f"{username}.{ext}")
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path

def get_avatar_base64(username):
    """Avatar लाई base64 मा (HTML मा देखाउन)"""
    path = get_avatar_path(username)
    if not path:
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def get_initials(username):
    """नामको initials निकाल्ने"""
    parts = username.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return username[:2].upper()

def render_avatar(username, size=44):
    """Avatar HTML render गर्ने"""
    b64 = get_avatar_base64(username)
    if b64:
        ext = "png"  # base64 मा type सोध्दैन
        return f'<img src="data:image/png;base64,{b64}" class="ds-avatar-img" style="width:{size}px;height:{size}px;" />'
    initials = get_initials(username)
    return f'<div class="ds-avatar-initials" style="width:{size}px;height:{size}px;font-size:{size//2.5}px;">{initials}</div>'

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
        "agent_tab": "🤖 Auto-Pilot Agent", "chat_welcome": "नमस्ते! के सोध्नु छ?", "chat_hint": "तल chat box मा प्रश्न लेख्नुहोस्",
        "chat_input": "प्रश्न लेख्नुहोस्...", "queries": "queries", "no_tags": "कोही छैन",
        "logout": "🚪 Logout", "ui_language": "UI भाषा", "database_ready": "Database तयार", "database_missing": "Database छैन",
        "actions": "Actions", "rebuild": "🔄 Rebuild", "chat_clear": "➕ New Chat", "export_chat": "💾 Export Chat",
        "no_chat": "कुनै chat छैन", "voice_settings": "🎤 Voice Settings", "auto_speak": "🔊 Auto-speak",
        "input_lang": "🎤 Input भाषा", "output_lang": "🔊 Output भाषा", "doc_tags": "🏷️ Document Tags",
        "chat_tag_filter": "Tag Filter", "filter_remove": "✖ हटाउनुहोस्", "filter_active": "Tag Filter Active",
        "filter_hint": "यी tags भएका PDF मा मात्र खोजिन्छ", "no_tags_available": "कुनै tags छैन",
        "admin_panel": "👑 Admin Panel", "users": "users", "deleted": "हटाइयो",
        "my_docs": "मेरो Documents", "upload_doc": "नयाँ Document Upload", "upload_hint": "PDF, DOCX, Image, TXT — कुनै पनि (एकैपटक धेरै हाल्न सकिन्छ)",
        "upload_process": "📤 Upload + Process", "uploading": "Upload हुँदै...", "processing": "Process हुँदै...",
        "files_saved": "files save भयो", "ai_ready": "AI तयार!", "my_files": "मेरा Files", "no_files": "कुनै document छैन।",
        "ask_docs": "💬 Documents बारे सोध्नुहोस्", "ask_hint": "प्रश्न लेख्नुहोस् वा 🎤 थिच्नुहोस्",
        "ask_placeholder": "जस्तै: यो document कसको हो?", "ask_btn": "🔍 सोध्नुहोस्", "clear_btn": "🗑️ Clear",
        "your_question": "तपाईंको प्रश्न", "ai_answer": "AI जवाफ", "thinking": "सोच्दै...", "analyzing": "विश्लेषण...",
        "image_analysis": "Image Analysis", "image_hint": "जस्तो सुकै image — AI ले बुझ्छ (एकैपटक धेरै हाल्न सकिन्छ)", "upload_image": "Image हाल्नुहोस्",
        "analysis_type": "Analysis प्रकार", "analyze_btn": "🔍 Analyze", "delete_btn": "🗑️ हटाउनुहोस्",
        "result": "परिणाम", "upload_prompt": "👈 Image upload गर्नुहोस्", "image_question": "💬 Image बारे सोध्नुहोस्",
        "image_placeholder": "जस्तै: कति amount छ?", "table_chart": "Table + Chart Analysis",
        "table_hint": "PDF, Excel, CSV, Image बाट tables निकालेर Excel मा बदल्नुहोस् (एकैपटक धेरै हाल्न सकिन्छ)", "pdf_select": "File चयन", "tables_found": "tables भेटियो",
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
        "no_history": "कुनै इतिहास छैन", "online": "अनलाइन", "messages": "सन्देशहरू", "copy_answer": "📋 Copy Answer",
        "friends": "साथीहरू", "add_friend": "साथी थप्नुहोस्", "pending": "पर्खाइमा", "accept": "स्वीकार", "reject": "अस्वीकार", "message": "सन्देश",
        "messenger": "Messenger", "active_now": "अहिले सक्रिय", "search": "खोज्नुहोस्...", "no_messages": "अहिलेसम्म कुनै सन्देश छैन", "type_msg": "सन्देश लेख्नुहोस्...",
        "share_btn": "📤 Share / Send", "send_to_messenger": "Messenger मा पठाउनुहोस्", "send_to_gmail": "Gmail मा पठाउनुहोस्",
        "enter_email": "इमेल ठेगाना लेख्नुहोस्", "send_email_btn": "📧 Email पठाउनुहोस्", "attached_file": "📎 फाइल संलग्न",
        "download_file": "⬇️ डाउनलोड गर्नुहोस्", "file_upload_label": "📎 फाइल अपलोड गर्नुहोस्",
        "send_success": "सफलतापूर्वक पठाइयो!", "share_report": "रिपोर्ट सेयर गर्नुहोस्",
        "team_share": "टिमलाई सेयर गर्नुहोस् (Multi-Select)", "select_members": "सदस्यहरू छान्नुहोस्",
        "data_edit_hint": "तपाईं यहाँ डाटा सिधै सम्पादन (Edit) गर्न सक्नुहुन्छ।", "save_changes": "परिवर्तन सेभ गर्नुहोस्",
        "back_to_chats": "🔙 च्याटहरूमा फर्कनुहोस्", "send_file": "फाइल पठाउनुहोस्",
        "img_gen_not_supported": "माफ गर्नुहोला, यो AI मोडेलले फोटो बनाउन (Generate) वा परिवर्तन गर्न (Edit) सक्दैन। यसले फोटो पढ्न र विश्लेषण गर्न मात्र सक्छ।",
        "forensic_btn": "🕵️‍♂️ Forensic Check (Fake Detector)", "forensic_hint": "यो फाइल वा तालिका फेक (Fake) हो कि असली (Original)? AI लाई सोध्नुहोस्।",
        "forensic_analyzing": "फाइल फोरेन्सिक विश्लेषण हुँदैछ...", "forensic_result": "🕵️‍♂️ फोरेन्सिक रिपोर्ट",
        "agent_goal": "तपाईंको लक्ष्य के हो?", "agent_goal_placeholder": "जस्तै: 'C:\\Users\\Dell\\Desktop\\company_brain\\docs भित्रको sample-table.pdf पढेर मलाई सारांश दिनु'",
        "agent_run_btn": "🚀 Auto-Pilot Agent लाई काम दिनुहोस्", "agent_working": "एजेन्ट आफैंले काम गर्दैछ...", "agent_success": "काम सम्पन्न भयो!",
        "agent_tools": "एजेन्टले प्रयोग गर्ने उपकरणहरू (Tools)", "agent_logs": "एजेन्टको कामको लग (Logs)",
        "agent_local_path": "स्थानीय कम्प्युटरको फाइल बाट काम गर्नुहोस् (Local Path)", "agent_path_hint": "C:\\Users\\... वा D:\\... को पूरा बाटो हाल्नुहोस्",
        "multi_upload_hint": "तपाईंले एकैपटक धेरै फाइलहरू छानेर अपलोड गर्न सक्नुहुन्छ।",
        "new_msg": "नयाँ सन्देश", "new_req": "नयाँ रिक्वेस्ट"
    },
    "en": {
        "chat_tab": "💬 Chat", "docs_tab": "📄 Documents", "image_tab": "🖼️ Image", "table_tab": "📊 Table + Chart",
        "agent_tab": "🤖 Auto-Pilot Agent", "chat_welcome": "Hello! What would you like to ask?", "chat_hint": "Type your question in the chat box below",
        "chat_input": "Type your question...", "queries": "queries", "no_tags": "None",
        "logout": "🚪 Logout", "ui_language": "UI Language", "database_ready": "Database Ready", "database_missing": "Database Missing",
        "actions": "Actions", "rebuild": "🔄 Rebuild", "chat_clear": "➕ New Chat", "export_chat": "💾 Export Chat",
        "no_chat": "No chat yet", "voice_settings": "🎤 Voice Settings", "auto_speak": "🔊 Auto-speak",
        "input_lang": "🎤 Input Language", "output_lang": "🔊 Output Language", "doc_tags": "🏷️ Document Tags",
        "chat_tag_filter": "Tag Filter", "filter_remove": "✖ Remove Filter", "filter_active": "Tag Filter Active",
        "filter_hint": "Searching only in tagged PDFs", "no_tags_available": "No tags",
        "admin_panel": "👑 Admin Panel", "users": "users", "deleted": "Deleted",
        "my_docs": "My Documents", "upload_doc": "Upload New Document", "upload_hint": "PDF, DOCX, Image, TXT — upload any (multiple files allowed)",
        "upload_process": "📤 Upload + Process", "uploading": "Uploading...", "processing": "Processing...",
        "files_saved": "files saved", "ai_ready": "AI Ready!", "my_files": "My Files", "no_files": "No documents yet.",
        "ask_docs": "💬 Ask about Documents", "ask_hint": "Type question or tap 🎤",
        "ask_placeholder": "e.g., Whose document is this?", "ask_btn": "🔍 Ask", "clear_btn": "🗑️ Clear",
        "your_question": "Your Question", "ai_answer": "AI Answer", "thinking": "Thinking...", "analyzing": "Analyzing...",
        "image_analysis": "Image Analysis", "image_hint": "Any image — AI understands (multiple allowed)", "upload_image": "Upload Image",
        "analysis_type": "Analysis Type", "analyze_btn": "🔍 Analyze", "delete_btn": "🗑️ Delete",
        "result": "Result", "upload_prompt": "👈 Upload an image", "image_question": "💬 Ask about Image",
        "image_placeholder": "e.g., What is the amount?", "table_chart": "Table + Chart Analysis",
        "table_hint": "Convert Tables from PDF, Excel, CSV, Image to Excel (multiple allowed)", "pdf_select": "Select File", "tables_found": "tables found",
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
        "no_history": "No history yet", "online": "Online", "messages": "messages", "copy_answer": "📋 Copy Answer",
        "friends": "Friends", "add_friend": "Add Friend", "pending": "Pending", "accept": "Accept", "reject": "Reject", "message": "Message",
        "messenger": "Messenger", "active_now": "Active Now", "search": "Search...", "no_messages": "No messages yet", "type_msg": "Type a message...",
        "share_btn": "📤 Share / Send", "send_to_messenger": "Send via Messenger", "send_to_gmail": "Send via Gmail",
        "enter_email": "Enter Email Address", "send_email_btn": "📧 Send Email", "attached_file": "📎 File Attached",
        "download_file": "⬇️ Download File", "file_upload_label": "📎 Upload File",
        "send_success": "Sent successfully!", "share_report": "Share Report",
        "team_share": "Share with Team (Multi-Select)", "select_members": "Select Members",
        "data_edit_hint": "You can edit the data directly here.", "save_changes": "Save Changes",
        "back_to_chats": "🔙 Back to Chats", "send_file": "Send File",
        "img_gen_not_supported": "Sorry, this AI model cannot generate or edit images. It can only analyze and read images.",
        "forensic_btn": "🕵️‍♂️ Forensic Check (Fake Detector)", "forensic_hint": "Is this file/table Fake or Original? Ask AI.",
        "forensic_analyzing": "Analyzing forensics...", "forensic_result": "🕵️‍♂️ Forensic Report",
        "agent_goal": "What is your goal?", "agent_goal_placeholder": "e.g., 'Read sample-table.pdf in C:\\Users\\Dell\\Desktop\\company_brain\\docs and summarize it'",
        "agent_run_btn": "🚀 Give Task to Auto-Pilot Agent", "agent_working": "Agent is working autonomously...", "agent_success": "Task Completed!",
        "agent_tools": "Agent Tools", "agent_logs": "Agent Work Logs",
        "agent_local_path": "Work with local computer files (Local Path)", "agent_path_hint": "Enter full path like C:\\Users\\... or D:\\...",
        "multi_upload_hint": "You can select and upload multiple files at once.",
        "new_msg": "New Message", "new_req": "New Request"
    },
    "hi": {
        "chat_tab": "💬 Chat", "docs_tab": "📄 Documents", "image_tab": "🖼️ Image", "table_tab": "📊 Table + Chart",
        "agent_tab": "🤖 Auto-Pilot Agent", "chat_welcome": "नमस्ते! क्या पूछना है?", "chat_hint": "नीचे chat box में प्रश्न लिखें",
        "chat_input": "प्रश्न लिखें...", "queries": "queries", "no_tags": "कोई नहीं",
        "logout": "🚪 Logout", "ui_language": "UI भाषा", "database_ready": "Database तैयार", "database_missing": "Database नहीं",
        "actions": "Actions", "rebuild": "🔄 Rebuild", "chat_clear": "➕ New Chat", "export_chat": "💾 Export Chat",
        "no_chat": "कोई chat नहीं", "voice_settings": "🎤 Voice Settings", "auto_speak": "🔊 Auto-speak",
        "input_lang": "🎤 Input भाषा", "output_lang": "🔊 Output भाषा", "doc_tags": "🏷️ Document Tags",
        "chat_tag_filter": "Tag Filter", "filter_remove": "✖ हटाएं", "filter_active": "Tag Filter Active",
        "filter_hint": "इन tags वाले PDF में खोज", "no_tags_available": "कोई tags नहीं",
        "admin_panel": "👑 Admin Panel", "users": "users", "deleted": "हटाया",
        "my_docs": "मेरे Documents", "upload_doc": "नया Document Upload", "upload_hint": "PDF, DOCX, Image, TXT — कोई भी (एक बार में कई फाइलें)",
        "upload_process": "📤 Upload + Process", "uploading": "Upload हो रहा...", "processing": "Process हो रहा...",
        "files_saved": "files save हुए", "ai_ready": "AI तैयार!", "my_files": "मेरी Files", "no_files": "कोई document नहीं।",
        "ask_docs": "💬 Documents के बारे में पूछें", "ask_hint": "प्रश्न लिखें या 🎤 दबाएं",
        "ask_placeholder": "जैसे: यह किसका document है?", "ask_btn": "🔍 पूछें", "clear_btn": "🗑️ Clear",
        "your_question": "आपका प्रश्न", "ai_answer": "AI जवाफ", "thinking": "सोच रहा हूँ...", "analyzing": "विश्लेषण...",
        "image_analysis": "Image Analysis", "image_hint": "कोई भी image — AI समझता है (कई फाइलें मिल सकती हैं)", "upload_image": "Image डालें",
        "analysis_type": "Analysis प्रकार", "analyze_btn": "🔍 Analyze", "delete_btn": "🗑️ हटाएं",
        "result": "परिणाम", "upload_prompt": "👈 Image upload करें", "image_question": "💬 Image के बारे में पूछें",
        "image_placeholder": "जैसे: कितना amount है?", "table_chart": "Table + Chart Analysis",
        "table_hint": "PDF, Excel, CSV, Image से tables निकालें और Excel बनाएं (कई फाइलें मिल सकती हैं)", "pdf_select": "File चुनें", "tables_found": "tables मिले",
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
        "no_history": "कोई इतिहास नहीं", "online": "ऑनलाइन", "messages": "संदेश", "copy_answer": "📋 Copy Answer",
        "friends": "दोस्त", "add_friend": "दोस्त जोड़ें", "pending": "लंबित", "accept": "स्वीकार", "reject": "अस्वीकार", "message": "संदेश",
        "messenger": "Messenger", "active_now": "अभी सक्रिय", "search": "खोजें...", "no_messages": "अभी तक कोई संदेश नहीं", "type_msg": "संदेश लिखें...",
        "share_btn": "📤 Share / Send", "send_to_messenger": "Messenger से भेजें", "send_to_gmail": "Gmail से भेजें",
        "enter_email": "ईमेल पता लिखें", "send_email_btn": "📧 Email भेजें", "attached_file": "📎 फाइल संलग्न",
        "download_file": "⬇️ डाउनलोड करें", "file_upload_label": "📎 फाइल अपलोड करें",
        "send_success": "सफलतापूर्वक भेजा गया!", "share_report": "रिपोर्ट शेयर करें",
        "team_share": "टीम के साथ शेयर करें (Multi-Select)", "select_members": "सदस्यों को चुनें",
        "data_edit_hint": "आप यहाँ डेटा सीधे एडिट कर सकते हैं।", "save_changes": "परिवर्तन सेव करें",
        "back_to_chats": "🔙 चैट्स पर वापस जाएं", "send_file": "फाइल भेजें",
        "img_gen_not_supported": "क्षमा करें, यह AI मॉडल छवि उत्पन्न या संपादित नहीं कर सकता। यह केवल छवियों को पढ़ और विश्लेषण कर सकता है।",
        "forensic_btn": "🕵️‍♂️ Forensic Check (Fake Detector)", "forensic_hint": "क्या यह फाइल/टेबल नकली (Fake) है या असली (Original)? AI से पूछें।",
        "forensic_analyzing": "फोरेंसिक विश्लेषण हो रहा है...", "forensic_result": "🕵️‍♂️ फोरेंसिक रिपोर्ट",
        "agent_goal": "आपका लक्ष्य क्या है?", "agent_goal_placeholder": "जैसे: 'C:\\Users\\Dell\\Desktop\\company_brain\\docs में sample-table.pdf पढ़ें और सारांश दें'",
        "agent_run_btn": "🚀 Auto-Pilot Agent को काम दें", "agent_working": "एजेंट खुद काम कर रहा है...", "agent_success": "काम पूरा हुआ!",
        "agent_tools": "एजेंट के टूल्स", "agent_logs": "एजेंट के काम के लॉग",
        "agent_local_path": "स्थानीय कंप्यूटर फ़ाइलों के साथ काम करें (Local Path)", "agent_path_hint": "C:\\Users\\... या D:\\... का पूरा पथ दर्ज करें",
        "multi_upload_hint": "आप एक बार में कई फाइलें चुनकर अपलोड कर सकते हैं।",
        "new_msg": "नया संदेश", "new_req": "नई रिक्वेस्ट"
    }
}

def t(key, lang=None):
    if lang is None: lang = st.session_state.get("ui_lang", "ne")
    return UI_TEXT.get(lang, UI_TEXT["ne"]).get(key, key)

# ============================================================
# Global CSS (Powerful Messenger Animation — FIXED)
# ============================================================
st.markdown("""
<style>
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .main .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; max-width: 1400px !important; }

    [data-testid="stSidebar"] { width: 380px !important; background: #ffffff; border-right: 1px solid #e8ecf1; }
    [data-testid="stSidebar"] .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }

    /* ---------- User Profile Card ---------- */
    .user-profile-card { display: flex; align-items: center; gap: 12px; padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; color: white; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); transition: all 0.3s ease; }
    .user-profile-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6); }
    .user-avatar { font-size: 2em; background: rgba(255,255,255,0.2); padding: 8px; border-radius: 50%; }
    .user-info h4 { margin: 0; font-size: 1.1em; font-weight: 700; }
    .user-info p { margin: 0; font-size: 0.8em; opacity: 0.9; }

    /* ============================================================ */
    /* 💬 MESSENGER ICON — Stable & Animated (Key-based selector)   */
    /* ============================================================ */
    @keyframes messenger-pulse {
        0%   { box-shadow: 0 0 0 0 rgba(0, 132, 255, 0.7), 0 4px 18px rgba(0,132,255,0.55); }
        50%  { box-shadow: 0 0 0 14px rgba(0, 132, 255, 0), 0 4px 18px rgba(0,132,255,0.55); }
        100% { box-shadow: 0 0 0 0 rgba(0, 132, 255, 0.7), 0 4px 18px rgba(0,132,255,0.55); }
    }

    /* Target sidebar button that contains 💬 emoji */
    div[data-testid="stSidebar"] button:has(p:contains("💬")) {
        background: linear-gradient(135deg, #0084ff 0%, #00c6ff 100%) !important;
        color: white !important;
        font-size: 26px !important;
        border-radius: 50% !important;
        width: 58px !important;
        height: 58px !important;
        min-height: 58px !important;
        border: 3px solid #ffffff !important;
        box-shadow: 0 4px 18px rgba(0, 132, 255, 0.55) !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.25s ease !important;
        animation: messenger-pulse 2.2s infinite ease-in-out !important;
    }
    div[data-testid="stSidebar"] button:has(p:contains("💬")):hover {
        transform: scale(1.12) rotate(-6deg) !important;
        box-shadow: 0 8px 28px rgba(0, 132, 255, 0.85) !important;
        animation: none !important;
    }

    /* ---------- Notification Badge ---------- */
    .messenger-icon-wrap { position: relative; display: inline-block; width: 100%; text-align: right; padding-right: 8px; margin-bottom: 8px; }
    .messenger-badge {
        position: absolute; top: -6px; right: 6px;
        background: #ff3b30; color: white;
        border-radius: 999px; padding: 3px 8px;
        font-size: 12px; font-weight: 800;
        border: 2px solid white;
        box-shadow: 0 2px 8px rgba(255, 59, 48, 0.55);
        animation: badge-bounce 1.4s infinite ease-in-out;
        z-index: 999; pointer-events: none;
    }
    @keyframes badge-bounce {
        0%, 100% { transform: scale(1); }
        50%      { transform: scale(1.18); }
    }

    /* ============================================================ */
    /* 💬 MESSENGER DIALOG — Header, Bubbles, Typing                */
    /* ============================================================ */
    .messenger-header {
        display: flex; align-items: center; gap: 10px;
        padding: 10px 12px; border-bottom: 1px solid #e8ecf1;
        background: #ffffff; border-radius: 12px 12px 0 0;
    }
    .msg-bubble {
        max-width: 82%; padding: 9px 14px; border-radius: 18px;
        font-size: 0.9em; line-height: 1.45; margin-bottom: 8px;
        word-wrap: break-word; position: relative;
        animation: msg-pop 0.18s ease-out;
    }
    @keyframes msg-pop {
        from { transform: translateY(4px); opacity: 0; }
        to   { transform: translateY(0); opacity: 1; }
    }
    .msg-user { align-self: flex-end; background: linear-gradient(135deg, #0084ff, #0073e6); color: white; border-bottom-right-radius: 4px; margin-left: auto; }
    .msg-ai   { align-self: flex-start; background: #f0f2f5; color: #050505; border-bottom-left-radius: 4px; margin-right: auto; }

    .typing-indicator {
        display: inline-flex; gap: 4px; padding: 10px 14px;
        background: #f0f2f5; border-radius: 18px;
        border-bottom-left-radius: 4px; width: fit-content;
        align-items: center; margin-right: auto;
    }
    .typing-indicator span {
        width: 7px; height: 7px; background: #90949c;
        border-radius: 50%; animation: typing-blink 1.4s infinite ease-in-out both;
    }
    .typing-indicator span:nth-child(2) { animation-delay: 0.18s; }
    .typing-indicator span:nth-child(3) { animation-delay: 0.36s; }
    @keyframes typing-blink {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
        40%           { transform: scale(1);   opacity: 1; }
    }

    /* ---------- Avatar with online dot ---------- */
    .avatar-circle {
        position: relative; width: 38px; height: 38px;
        border-radius: 50%;
        background: linear-gradient(135deg, #0084ff, #0073e6);
        display: flex; align-items: center; justify-content: center;
        color: white; font-weight: 700; font-size: 16px; flex-shrink: 0;
    }
    .avatar-circle .online-dot {
        position: absolute; bottom: 0; right: 0;
        width: 11px; height: 11px; background: #31a24c;
        border: 2px solid white; border-radius: 50%;
    }

    /* ---------- Tabs ---------- */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%); padding: 8px; border-radius: 14px; border: 1px solid #e8ecf1; box-shadow: 0 2px 10px rgba(0,0,0,0.04); margin-bottom: 20px; }
    .stTabs [data-baseweb="tab"] { height: 44px; padding: 0 20px; background: transparent; border-radius: 10px; font-weight: 600; font-size: 0.95rem; color: #555; border: none; transition: all 0.2s ease; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #0084ff 0%, #0073e6 100%) !important; color: white !important; }

    /* ---------- Misc UI ---------- */
    .empty-state { text-align: center; padding: 40px 20px; color: #888; }
    .empty-state .icon { font-size: 4em; margin-bottom: 15px; }
    .empty-state h3 { font-size: 1.3em; color: #333; margin-bottom: 8px; font-weight: 600; }
    .empty-state p { font-size: 0.95em; color: #777; }
    .chat-q-box { background: #f7f7f8; padding: 16px 20px; border-radius: 12px; border: 1px solid #e8ecf1; margin: 15px 0 10px 0; font-weight: 500; }
    .chat-a-box { background: white; padding: 20px; border-radius: 12px; border: 1px solid #e8ecf1; margin: 10px 0; line-height: 1.7; white-space: pre-wrap; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }

    @media (max-width: 768px) {
        [data-testid="stSidebar"] { width: 100% !important; }
        .main .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
    }
    
        /* ============================================================ */
    /* 🎨 SIDEBAR — PREMIUM GLASSMORPHISM STYLE                     */
    /* ============================================================ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f5f7ff 0%, #eef2fc 50%, #e8edfa 100%) !important;
        border-right: 2px solid rgba(102, 126, 234, 0.15) !important;
        box-shadow: 2px 0 20px rgba(102, 126, 234, 0.08);
        resize: horizontal;
        overflow: auto;
        min-width: 280px;
        max-width: 520px;
    }
    [data-testid="stSidebar"] .block-container {
        padding: 12px 14px 16px 14px !important;
    }
    [data-testid="stSidebar"] hr {
        margin: 10px 0 !important;
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, #d0d8f0, transparent) !important;
    }

    /* ---- 🔷 PROFILE CARD ---- */
    .ds-profile {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 14px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 60%, #8b5cf6 100%);
        border-radius: 16px;
        color: white;
        margin-bottom: 12px;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.35), inset 0 1px 0 rgba(255,255,255,0.2);
        position: relative;
        overflow: hidden;
        transition: transform 0.3s ease;
    }
    .ds-profile::before {
        content: '';
        position: absolute;
        top: -50%; right: -30%;
        width: 140px; height: 140px;
        background: radial-gradient(circle, rgba(255,255,255,0.15), transparent 70%);
        border-radius: 50%;
    }
    .ds-profile::after {
        content: '';
        position: absolute;
        bottom: -40%; left: -20%;
        width: 100px; height: 100px;
        background: radial-gradient(circle, rgba(255,255,255,0.1), transparent 70%);
        border-radius: 50%;
    }
    .ds-profile:hover { transform: translateY(-2px); }
    .ds-avatar-wrap {
        position: relative;
        flex-shrink: 0;
        z-index: 1;
    }
    .ds-avatar-wrap .online-dot {
        position: absolute;
        bottom: 0; right: 0;
        width: 13px; height: 13px;
        background: #31a24c;
        border: 2.5px solid white;
        border-radius: 50%;
        box-shadow: 0 0 0 3px rgba(49,162,76,0.2);
        animation: online-pulse 2s infinite;
    }
    @keyframes online-pulse {
        0%, 100% { box-shadow: 0 0 0 3px rgba(49,162,76,0.2); }
        50% { box-shadow: 0 0 0 6px rgba(49,162,76,0.05); }
    }
    .ds-avatar-img, .ds-avatar-initials {
        width: 46px; height: 46px;
        border-radius: 50%;
        object-fit: cover;
        border: 2.5px solid rgba(255,255,255,0.6);
        flex-shrink: 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    .ds-avatar-initials {
        background: linear-gradient(135deg, #5a6fd8, #6a4a9c);
        color: white;
        display: flex; align-items: center; justify-content: center;
        font-size: 17px; font-weight: 800;
        letter-spacing: 0.5px;
    }
    .ds-info { flex-grow: 1; overflow: hidden; z-index: 1; }
    .ds-info h4 {
        margin: 0; font-size: 1em; font-weight: 700;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        text-shadow: 0 1px 2px rgba(0,0,0,0.15);
    }
    .ds-info p {
        margin: 4px 0 0 0; font-size: 0.72em; opacity: 0.95;
        display: flex; align-items: center; gap: 6px;
    }
    .ds-role-badge {
        background: rgba(255,255,255,0.28);
        padding: 2px 8px; border-radius: 10px;
        font-size: 0.62em; font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        backdrop-filter: blur(4px);
    }

    /* ---- 📑 SECTION HEADERS ---- */
    .ds-section {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 6px 4px;
        margin: 12px 0 6px 0;
        font-size: 0.7em;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #5a6a8a;
        border-bottom: 1px solid #e1e6f0;
    }
    .ds-section .ds-badge {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.85em;
        margin-left: auto;
        box-shadow: 0 2px 6px rgba(102,126,234,0.4);
    }

    /* ---- 🧠 MEMORY HEADER ---- */
    .memory-header {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        color: white;
        font-weight: 700;
        font-size: 0.85em;
        margin-bottom: 8px;
        box-shadow: 0 4px 14px rgba(102, 126, 234, 0.4);
        position: relative;
        overflow: hidden;
    }
    .memory-header::after {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        animation: shimmer 3s infinite;
    }
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    .memory-header .count {
        background: rgba(255,255,255,0.3);
        padding: 2px 9px;
        border-radius: 10px;
        font-size: 0.8em;
        margin-left: auto;
        font-weight: 800;
        backdrop-filter: blur(4px);
    }

    /* ---- 📌 MEMORY ITEMS ---- */
    .memory-item {
        display: flex;
        align-items: flex-start;
        gap: 9px;
        padding: 10px 12px;
        background: white;
        border-radius: 11px;
        margin-bottom: 6px;
        border: 1.5px solid #e8ecf4;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        font-size: 0.78em;
        line-height: 1.4;
        color: #2c3e50;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        position: relative;
        overflow: hidden;
    }
    .memory-item::before {
        content: '';
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 3px;
        background: linear-gradient(180deg, #667eea, #764ba2);
        opacity: 0;
        transition: opacity 0.2s;
    }
    .memory-item:hover {
        background: linear-gradient(135deg, #f8faff, #f0f4ff);
        border-color: #667eea;
        transform: translateX(3px);
        box-shadow: 0 4px 14px rgba(102, 126, 234, 0.18);
    }
    .memory-item:hover::before { opacity: 1; }
    .memory-item .m-icon {
        font-size: 1.15em;
        flex-shrink: 0;
        margin-top: 1px;
    }
    .memory-item .m-text { flex-grow: 1; word-break: break-word; font-weight: 500; }
    .memory-item .m-type {
        font-size: 0.7em;
        color: #8892b0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
        display: block;
        font-weight: 700;
    }
    .memory-empty {
        text-align: center;
        padding: 20px 12px;
        color: #8892b0;
        font-size: 0.82em;
        font-style: italic;
        background: linear-gradient(135deg, #f8faff, #f0f4ff);
        border-radius: 10px;
        border: 1px dashed #d0d8f0;
    }

    /* ---- 📚 HISTORY TABS ---- */
    [data-testid="stSidebar"] .stTabs [data-baseweb="tab-list"] {
        gap: 3px;
        background: linear-gradient(135deg, #eef2fc, #e5ebf8);
        padding: 4px;
        border-radius: 10px;
        margin-bottom: 8px;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
    }
    [data-testid="stSidebar"] .stTabs [data-baseweb="tab"] {
        height: 36px;
        padding: 0 10px;
        font-size: 0.9em;
        border-radius: 7px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    [data-testid="stSidebar"] .stTabs [data-baseweb="tab"]:hover {
        background: rgba(102, 126, 234, 0.1);
    }
    [data-testid="stSidebar"] .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
        box-shadow: 0 3px 10px rgba(102,126,234,0.4);
    }

    /* ---- 🎯 HISTORY ITEMS ---- */
    .ds-history-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 9px 12px;
        background: white;
        border-radius: 9px;
        margin-bottom: 5px;
        border: 1.5px solid #e8ecf4;
        font-size: 0.8em;
        color: #2c3e50;
        transition: all 0.2s ease;
        cursor: pointer;
        font-weight: 500;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .ds-history-item:hover {
        background: linear-gradient(135deg, #f8faff, #f0f4ff);
        border-color: #667eea;
        transform: translateX(3px);
        box-shadow: 0 3px 10px rgba(102,126,234,0.15);
    }
    .ds-history-item .ds-h-icon { flex-shrink: 0; font-size: 1.1em; }
    .ds-history-item .ds-h-text {
        flex-grow: 1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .ds-empty {
        text-align: center;
        padding: 16px 10px;
        color: #8892b0;
        font-size: 0.8em;
        font-style: italic;
        background: linear-gradient(135deg, #f8faff, #f0f4ff);
        border-radius: 9px;
        border: 1px dashed #d0d8f0;
    }

    /* ---- 🔍 SEARCH BAR ---- */
    [data-testid="stSidebar"] .stTextInput input {
        background: white !important;
        border: 1.5px solid #e1e6f0 !important;
        border-radius: 10px !important;
        padding: 9px 14px !important;
        font-size: 0.85em !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
    }
    [data-testid="stSidebar"] .stTextInput input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 4px rgba(102,126,234,0.15) !important;
        background: #fafbff !important;
    }

    /* ---- 🎨 BUTTONS ---- */
    [data-testid="stSidebar"] .stButton > button {
        border-radius: 9px;
        font-weight: 600;
        transition: all 0.25s ease;
        border: 1.5px solid #e1e6f0;
        background: white;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(102,126,234,0.2);
        border-color: #667eea;
        background: linear-gradient(135deg, #f8faff, #f0f4ff);
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        box-shadow: 0 3px 12px rgba(102,126,234,0.4);
    }

    /* ---- 💬 MESSENGER ICON ---- */
    div[data-testid="stSidebar"] button[kind="secondary"]:has(p:contains("💬")) {
        background: linear-gradient(135deg, #0084ff, #00c6ff) !important;
        color: white !important;
        font-size: 24px !important;
        border-radius: 50% !important;
        width: 52px !important;
        height: 52px !important;
        min-height: 52px !important;
        border: 3px solid white !important;
        box-shadow: 0 6px 20px rgba(0, 132, 255, 0.5) !important;
        padding: 0 !important;
        margin: 6px auto !important;
        display: block !important;
        animation: messenger-pulse 2.2s infinite ease-in-out !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stSidebar"] button[kind="secondary"]:has(p:contains("💬")):hover {
        transform: scale(1.12) rotate(-6deg) !important;
        box-shadow: 0 10px 28px rgba(0, 132, 255, 0.7) !important;
        animation: none !important;
    }
    @keyframes messenger-pulse {
        0%, 100% { box-shadow: 0 6px 20px rgba(0,132,255,0.5), 0 0 0 0 rgba(0,132,255,0.5); }
        50% { box-shadow: 0 6px 20px rgba(0,132,255,0.5), 0 0 0 14px rgba(0,132,255,0); }
    }

    /* ---- 🏷️ BADGE ---- */
    .messenger-icon-wrap {
        position: relative;
        display: inline-block;
        width: 100%;
        text-align: center;
        margin-bottom: 8px;
    }
    .messenger-badge {
        position: absolute;
        top: -2px;
        right: calc(50% - 32px);
        background: linear-gradient(135deg, #ff3b30, #ff6b6b);
        color: white;
        border-radius: 999px;
        padding: 3px 9px;
        font-size: 11px;
        font-weight: 800;
        border: 2px solid white;
        box-shadow: 0 3px 10px rgba(255, 59, 48, 0.5);
        animation: badge-bounce 1.4s infinite ease-in-out;
        z-index: 999;
        pointer-events: none;
    }
    @keyframes badge-bounce {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.18); }
    }

    /* ---- 🎯 FOOTER ---- */
    .ds-footer {
        display: flex;
        flex-direction: column;
        gap: 5px;
        padding: 12px 14px;
        background: linear-gradient(135deg, #ffffff, #f8faff);
        border-radius: 12px;
        border: 1.5px solid #e1e6f0;
        margin-top: 10px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(102,126,234,0.08);
    }
    .ds-footer .ds-version {
        font-size: 0.85em;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .ds-footer .ds-links {
        display: flex;
        justify-content: center;
        gap: 14px;
        font-size: 0.7em;
    }
    .ds-footer .ds-links a {
        color: #8892b0;
        text-decoration: none;
        transition: all 0.2s ease;
        font-weight: 600;
    }
    .ds-footer .ds-links a:hover {
        color: #667eea;
        transform: translateY(-1px);
    }

    /* ---- ⚙️ EXPANDERS ---- */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        font-size: 0.82em !important;
        font-weight: 700 !important;
        background: white !important;
        border-radius: 10px !important;
        padding: 8px 12px !important;
        border: 1.5px solid #e1e6f0 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
    }
    [data-testid="stSidebar"] .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #f8faff, #f0f4ff) !important;
        border-color: #667eea !important;
    }
    [data-testid="stSidebar"] details[open] .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f0f4ff, #e8edfa) !important;
        border-color: #667eea !important;
        color: #667eea !important;
    }

    /* ---- 📱 RESPONSIVE ---- */
    @media (max-width: 768px) {
        [data-testid="stSidebar"] { min-width: 100% !important; max-width: 100% !important; }
    }
    
    /* ============================================================ */
    /* 👤 FACEBOOK-STYLE PROFILE CARD                               */
    /* ============================================================ */
    .fb-profile-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 60%, #8b5cf6 100%);
        border-radius: 16px;
        padding: 14px;
        color: white;
        margin-bottom: 10px;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.35), inset 0 1px 0 rgba(255,255,255,0.2);
        position: relative;
        overflow: hidden;
    }
    .fb-profile-card::before {
        content: '';
        position: absolute;
        top: -50%; right: -30%;
        width: 140px; height: 140px;
        background: radial-gradient(circle, rgba(255,255,255,0.15), transparent 70%);
        border-radius: 50%;
    }
    .fb-profile-card .fb-row {
        display: flex;
        align-items: center;
        gap: 12px;
        position: relative;
        z-index: 1;
    }
    .fb-profile-card .fb-avatar-wrap {
        position: relative;
        flex-shrink: 0;
    }
    .fb-profile-card .fb-avatar-wrap .fb-online-dot {
        position: absolute;
        bottom: 0; right: 0;
        width: 13px; height: 13px;
        background: #31a24c;
        border: 2.5px solid white;
        border-radius: 50%;
        box-shadow: 0 0 0 3px rgba(49,162,76,0.25);
        animation: fb-online-pulse 2s infinite;
    }
    @keyframes fb-online-pulse {
        0%, 100% { box-shadow: 0 0 0 3px rgba(49,162,76,0.25); }
        50% { box-shadow: 0 0 0 7px rgba(49,162,76,0.05); }
    }
    .fb-avatar-img, .fb-avatar-initials {
        width: 50px; height: 50px;
        border-radius: 50%;
        object-fit: cover;
        border: 2.5px solid rgba(255,255,255,0.6);
        flex-shrink: 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        transition: transform 0.2s;
    }
    .fb-avatar-img:hover, .fb-avatar-initials:hover {
        transform: scale(1.08);
        border-color: white;
    }
    .fb-avatar-initials {
        background: linear-gradient(135deg, #5a6fd8, #6a4a9c);
        color: white;
        display: flex; align-items: center; justify-content: center;
        font-size: 19px; font-weight: 800;
    }
    .fb-profile-card .fb-info {
        flex-grow: 1;
        overflow: hidden;
    }
    .fb-profile-card .fb-info h4 {
        margin: 0; font-size: 1em; font-weight: 700;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .fb-profile-card .fb-info p {
        margin: 4px 0 0 0; font-size: 0.72em; opacity: 0.95;
        display: flex; align-items: center; gap: 6px;
    }
    .fb-profile-card .fb-role-badge {
        background: rgba(255,255,255,0.28);
        padding: 2px 8px; border-radius: 10px;
        font-size: 0.62em; font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    .fb-profile-card .fb-logout-btn {
        position: absolute;
        top: 10px; right: 10px;
        background: rgba(255,255,255,0.2);
        border: 1.5px solid rgba(255,255,255,0.35);
        border-radius: 8px;
        padding: 4px 8px;
        font-size: 0.8em;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
        color: white;
        z-index: 2;
    }
    .fb-profile-card .fb-logout-btn:hover {
        background: rgba(255,59,48,0.8);
        border-color: #ff3b30;
        transform: scale(1.05);
    }
    .fb-avatar-hint {
        position: absolute;
        bottom: -2px; left: 50%;
        transform: translateX(-50%);
        background: rgba(0,0,0,0.5);
        color: white;
        padding: 1px 6px;
        border-radius: 6px;
        font-size: 0.55em;
        font-weight: 700;
        white-space: nowrap;
        opacity: 0;
        transition: opacity 0.2s;
        pointer-events: none;
    }
    .fb-avatar-wrap:hover .fb-avatar-hint {
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# ✅ Client Delivery Download (ग्राहकले लिंक खोल्दा)
# ============================================================
delivery_token = st.query_params.get("delivery")
if delivery_token:
    from file_delivery import get_delivery_file
    file_data = get_delivery_file(delivery_token)
    
    if file_data:
        st.title("📦 तपाईंको फाइल तयार छ")
        st.markdown(f"**प्रोजेक्ट:** {file_data['project_name']}")
        st.markdown(f"**फाइल:** {file_data['file_name']}")
        
        with open(file_data["file_path"], "rb") as f:
            st.download_button(
                "⬇️ फाइल डाउनलोड गर्नुहोस्",
                data=f.read(),
                file_name=file_data["file_name"],
                use_container_width=True
            )
    else:
        st.error("❌ यो लिंक अवैध छ वा म्याद सकिएको छ।")
    st.stop()
    
# ============================================================
# Login Check
# ============================================================
if "user" not in st.session_state:
    st.session_state.user = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ✅ Flag जाँच — login भए dashboard, नभए login page
if st.session_state.user is None or not st.session_state.logged_in:
    from login import login_page
    login_page()
    st.stop()

# ============================================================
# 🔑 PASSWORD RESET PAGE (Query param बाट — Login भन्दा अघि)
# ============================================================
if st.session_state.user is None:
    reset_token = st.query_params.get("reset_token")
    if reset_token:
        from auth import verify_reset_token, consume_reset_token
        valid, result = verify_reset_token(reset_token)

        st.markdown("## 🔑 नयाँ Password सेट गर्नुहोस्")

        if not valid:
            st.error(f"❌ {result}")
            st.info("Reset link expired वा अवैध छ। फेरि अनुरोध गर्नुहोस्।")
            if st.button("🔙 Login page"):
                st.query_params.clear()
                st.rerun()
        else:
            st.success(f"✅ Token valid — **{result}** को लागि")
            with st.form("reset_password_form"):
                new_pass = st.text_input("🔑 नयाँ Password", type="password", key="reset_new_pass")
                new_pass2 = st.text_input("🔑 Confirm Password", type="password", key="reset_new_pass2")
                submit_reset = st.form_submit_button("✅ Password Reset", type="primary", use_container_width=True)

                if submit_reset:
                    if not new_pass or not new_pass2:
                        st.error("⚠️ दुवै field भर्नुहोस्")
                    elif new_pass != new_pass2:
                        st.error("❌ Password मिलेन")
                    elif len(new_pass) < 6:
                        st.error("❌ Password कम्तिमा ६ अक्षर")
                    else:
                        ok, msg = consume_reset_token(reset_token, new_pass)
                        if ok:
                            st.success(f"✅ {msg}")
                            st.info("अब login गर्नुहोस्।")
                            time.sleep(1)
                            st.query_params.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

            if st.button("🔙 Login page", key="back_to_login"):
                st.query_params.clear()
                st.rerun()

        st.stop()   # ✅ यहाँ रोक्ने — login page नदेखाउन

# ============================================================
# LOGIN PAGE
# ============================================================
if st.session_state.user is None:
    from login import login_page
    login_page()
    st.stop()
    
# ✅ Audit: login
if st.session_state.user:
    log_action(st.session_state.user, "LOGIN", status="success")    

# ============================================================
# Database Setup (SQLite)
# ============================================================
DB_FILE = "pdf_brain.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    friends TEXT,
                    requests TEXT,
                    last_read TEXT
                )''')
    try:
        c.execute("SELECT last_read FROM users LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE users ADD COLUMN last_read TEXT")
        
    c.execute('''CREATE TABLE IF NOT EXISTS dm_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT,
                    receiver TEXT,
                    message TEXT,
                    file_name TEXT,
                    file_path TEXT,
                    timestamp TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS shared_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT,
                    receivers TEXT,
                    title TEXT,
                    content TEXT,
                    timestamp TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# ============================================================
# Database Helper Functions
# ============================================================
def register_user_in_db(username):
    conn = get_db_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT OR IGNORE INTO users (username, friends, requests, last_read) VALUES (?, ?, ?, ?)", (username, json.dumps([]), json.dumps([]), now))
    conn.commit()
    conn.close()

def get_user_data(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT friends, requests, last_read FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "friends": json.loads(row["friends"]), 
            "requests": json.loads(row["requests"]),
            "last_read": row["last_read"] if row["last_read"] else "1970-01-01T00:00:00"
        }
    return {"friends": [], "requests": [], "last_read": "1970-01-01T00:00:00"}

def update_user_data(username, friends, requests):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET friends = ?, requests = ? WHERE username = ?", (json.dumps(friends), json.dumps(requests), username))
    conn.commit()
    conn.close()

def update_last_read(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET last_read = ? WHERE username = ?", (datetime.now().isoformat(), username))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT username FROM users")
    rows = c.fetchall()
    conn.close()
    return [row["username"] for row in rows]

def send_friend_request(from_user, to_user):
    to_user_data = get_user_data(to_user)
    if from_user not in to_user_data["friends"] and from_user not in to_user_data["requests"]:
        to_user_data["requests"].append(from_user)
        update_user_data(to_user, to_user_data["friends"], to_user_data["requests"])
        return True
    return False

def accept_friend_request(user, from_user):
    user_data = get_user_data(user)
    from_user_data = get_user_data(from_user)
    if from_user in user_data["requests"]:
        user_data["requests"].remove(from_user)
        user_data["friends"].append(from_user)
        from_user_data["friends"].append(user)
        update_user_data(user, user_data["friends"], user_data["requests"])
        update_user_data(from_user, from_user_data["friends"], from_user_data["requests"])
        return True
    return False

def get_dm_history_db(u1, u2):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''SELECT sender, message, file_name, file_path, timestamp FROM dm_messages 
                 WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?) 
                 ORDER BY timestamp ASC''', (u1, u2, u2, u1))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def send_dm_db(from_user, to_user, text="", file_name=None, file_path=None):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO dm_messages (sender, receiver, message, file_name, file_path, timestamp) 
                 VALUES (?, ?, ?, ?, ?, ?)''', (from_user, to_user, text, file_name, file_path, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_unread_count(username, user_data):
    last_read = user_data["last_read"]
    unread_reqs = len(user_data["requests"])
    unread_msgs = 0
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT count(*) FROM dm_messages WHERE receiver = ? AND timestamp > ?", (username, last_read))
    row = c.fetchone()
    if row: unread_msgs = row[0]
    conn.close()
    return unread_msgs, unread_reqs

register_user_in_db(st.session_state.user)

# ============================================================
# Other File-Based Helpers (History)
# ============================================================
HISTORY_DIR = "history_data"
os.makedirs(HISTORY_DIR, exist_ok=True)
UPLOAD_DIR = "messenger_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_hist_file(username): return os.path.join(HISTORY_DIR, f"{username}.json")
def load_history(username):
    path = get_hist_file(username)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: pass
    return {"chat": {}, "docs": {}, "image": {}, "table": {}}

def save_history(username, data):
    with open(get_hist_file(username), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_to_history(username, category, item_id, title, data_payload, extra_state=None):
    history = load_history(username)
    if category not in history: history[category] = {}
    if item_id not in history[category]:
        history[category][item_id] = {"title": title[:30] + "..." if len(title) > 30 else title, "timestamp": datetime.now().isoformat()}
    history[category][item_id]["data"] = data_payload
    history[category][item_id]["timestamp"] = datetime.now().isoformat()
    if extra_state: history[category][item_id]["extra_state"] = extra_state
    if len(history[category]) > 20:
        oldest = min(history[category].keys(), key=lambda k: history[category][k]["timestamp"])
        del history[category][oldest]
    save_history(username, history)

def delete_history_item(username, category, item_id):
    history = load_history(username)
    if item_id in history.get(category, {}):
        del history[category][item_id]
        save_history(username, history)

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
        MODEL = "gemini-3.5-flash-lite"
        
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
        from cost_tracker import track_cost  # ✅ यो थप्नुहोस्
        from user_manager import get_user_stats
        from google import genai
        from dotenv import load_dotenv
        load_dotenv()
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        MODEL = "gemini-3.5-flash-lite"
        
        # ✅ यहाँ खर्च ट्र्याक गर्ने
        track_cost(username, service="Gemini", amount=0.0001)
        
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

def forensic_check(file_type, data=None, file_path=None, lang="ne"):
    try:
        from google import genai
        from dotenv import load_dotenv
        load_dotenv()
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        MODEL = "gemini-3.5-flash-lite"
        lang_instruction = "Answer strictly in Nepali." if lang == "ne" else ("Answer strictly in Hindi." if lang == "hi" else "Answer strictly in English.")
        
        if file_type == "image" and file_path:
            from image_analyzer import detect_mime_type
            from google.genai import types
            with open(file_path, "rb") as f: img_data = f.read()
            mime = detect_mime_type(file_path)
            prompt = f"You are a Forensic Image Analyst. Analyze this image carefully.\n\n🔍 Check for:\n1. Is this image AI-generated or heavily edited? (Look for weird lighting, unnatural shadows, blurry edges, extra fingers, etc.)\n2. Are there any signs of tampering (Photoshop)?\n3. Does the text (if any) look real?\n\n⚠️ Give a verdict: Is it likely FAKE or ORIGINAL? Give reasons.\n\n{lang_instruction}"
            response = client.models.generate_content(model=MODEL, contents=[types.Part.from_bytes(data=img_data, mime_type=mime), prompt])
            return response.text
        elif file_type == "table" and data is not None:
            if isinstance(data, pd.DataFrame): table_text = data.head(50).to_string(index=False)
            else: table_text = str(data)[:3000]
            prompt = f"You are a Forensic Data Analyst. Analyze this table data carefully.\n\n📊 Table Data:\n{table_text}\n\n🔍 Check for:\n1. Do the calculations match? (Sum, Total, etc.)\n2. Are there duplicate entries or weird numbers?\n3. Does the data look tampered or manually edited?\n\n⚠️ Give a verdict: Is it likely FAKE or ORIGINAL? Give reasons.\n\n{lang_instruction}"
            response = client.models.generate_content(model=MODEL, contents=prompt)
            return response.text
    except Exception as e:
        return f"❌ Error: {str(e)[:200]}"

def tool_search_files(folder_path: str):
    if not os.path.exists(folder_path): return f"Folder '{folder_path}' not found."
    try:
        files = os.listdir(folder_path)
        return f"Files in {folder_path}: {files[:20]}" 
    except Exception as e:
        return f"Error reading folder: {e}"

def tool_read_any_file(file_path: str):
    if not os.path.exists(file_path): return "File not found."
    file_ext = file_path.lower().split(".")[-1]
    try:
        if file_ext == "pdf":
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages[:5]: text += page.extract_text() + "\n"
            return text[:5000]
        elif file_ext in ["xlsx", "xls"]:
            df = pd.read_excel(file_path)
            return df.head(30).to_string(index=False)
        elif file_ext == "csv":
            df = pd.read_csv(file_path)
            return df.head(30).to_string(index=False)
        elif file_ext in ["txt", "md", "py", "json"]:
            with open(file_path, "r", encoding="utf-8") as f: return f.read()[:5000]
        else:
            return f"Unsupported file type: .{file_ext}. Only PDF, Excel, CSV, TXT are supported for text extraction."
    except Exception as e:
        return f"Error reading file: {e}"
    
def tool_web_search(query: str) -> str:
    """इन्टरनेटबाट ताजा जानकारी खोज्ने"""
    try:
        from duckduckgo_search import DDGS
        # ✅ नयाँ संस्करण अनुसार
        results = list(DDGS().text(query, max_results=5))
        
        if not results:
            return "कुनै नतिजा भेटिएन।"
            
        output = f"🔍 '{query}' को खोज नतिजा:\n\n"
        for i, res in enumerate(results, 1):
            output += f"{i}. **{res.get('title', 'No title')}**\n{res.get('body', 'No body')}\nलिङ्क: {res.get('href', '#')}\n\n"
        return output
    except Exception as e:
        return f"Search error: {e}"

def tool_read_webpage(url: str) -> str:
    """वेबसाइटको लिङ्क खोलेर भित्रको टेक्स्ट पढ्ने"""
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # स्क्रिप्ट र स्टाइल हटाउने
        for script in soup(["script", "style"]):
            script.decompose()
            
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return clean_text[:4000]  # पहिलो ४००० अक्षर मात्र (AI को सीमा)
    except Exception as e:
        return f"Webpage read error: {e}"    
    
# ============================================================
# AUTO-PILOT AGENT — Powerful Tools (v2)
# ============================================================
import subprocess
import shlex

# ============================================================
# सुरक्षा allowlist — एजेन्टले यी फोल्डर भित्र मात्र काम गर्न सक्छ
# ============================================================
_username = os.getenv("USERNAME") or os.getenv("USER") or "Dell"

AGENT_ALLOWED_ROOTS = [
    # प्रोजेक्ट फोल्डरहरू
    os.path.abspath("docs"),
    os.path.abspath("messenger_uploads"),
    os.path.abspath("history_data"),
    os.path.abspath("temp_tables"),
    os.path.abspath("temp_images"),
    os.path.abspath("temp_audio"),

    # ✅ Windows का सामान्य फोल्डरहरू (परीक्षणका लागि)
    os.path.abspath(os.path.join("C:\\Users", _username, "Downloads")),
    os.path.abspath(os.path.join("C:\\Users", _username, "Desktop")),
    os.path.abspath(os.path.join("C:\\Users", _username, "Documents")),
]

def _is_path_allowed(path: str) -> bool:
    """जाँच गर्नुहोस् कि path allowlist भित्र छ"""
    try:
        abs_path = os.path.abspath(path)
        for root in AGENT_ALLOWED_ROOTS:
            if abs_path.startswith(root + os.sep) or abs_path == root:
                return True
        return False
    except Exception:
        return False

def tool_write_file(file_path: str, content: str) -> str:
    """फाइलमा लेख्नुहोस् (allowlist भित्र मात्र)"""
    if not _is_path_allowed(file_path):
        return f"❌ Access denied: '{file_path}' is outside allowed folders. Allowed: {AGENT_ALLOWED_ROOTS}"
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ Written {len(content)} chars to {file_path}"
    except Exception as e:
        return f"❌ Write error: {e}"

def tool_run_python(code: str, timeout_sec: int = 30) -> str:
    """Python कोड चलाउनुहोस् (subprocess, timeout सहित)"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=timeout_sec,
            cwd=os.path.abspath(".")
        )
        output = result.stdout[-3000:] if result.stdout else ""
        error = result.stderr[-1500:] if result.stderr else ""
        if result.returncode == 0:
            return f"✅ Output:\n{output}" if output else "✅ Executed (no output)"
        return f"❌ Exit {result.returncode}\nSTDOUT: {output}\nSTDERR: {error}"
    except subprocess.TimeoutExpired:
        return f"❌ Timeout after {timeout_sec}s"
    except Exception as e:
        return f"❌ Error: {e}"

def tool_list_directory(folder_path: str) -> str:
    """फोल्डरको सामग्री देखाउनुहोस् (allowlist भित्र)"""
    if not _is_path_allowed(folder_path):
        return f"❌ Access denied: '{folder_path}'"
    if not os.path.exists(folder_path):
        return f"Folder not found: {folder_path}"
    try:
        items = []
        for name in sorted(os.listdir(folder_path))[:50]:
            full = os.path.join(folder_path, name)
            if os.path.isdir(full):
                items.append(f"📁 {name}/")
            else:
                size = os.path.getsize(full)
                items.append(f"📄 {name} ({size} bytes)")
        return "\n".join(items) if items else "(empty folder)"
    except Exception as e:
        return f"❌ Error: {e}"

def tool_summarize_pdf(file_path: str, max_pages: int = 10) -> str:
    """PDF को सारांश (पहिलो N पृष्ठ)"""
    if not _is_path_allowed(file_path):
        return f"❌ Access denied: '{file_path}'"
    if not os.path.exists(file_path):
        return f"File not found: {file_path}"
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages[:max_pages]:
            text += page.extract_text() + "\n"
        if not text.strip():
            return "PDF has no extractable text."
        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            resp = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=f"Summarize this PDF content in Nepali (or English if content is English):\n\n{text[:8000]}"
            )
            return resp.text
        except Exception:
            return f"Extracted text (first 2000 chars):\n{text[:2000]}"
    except Exception as e:
        return f"❌ Error: {e}"
    
def tool_analyze_image(file_path: str, question: str = "What is in this image? Describe in detail.") -> str:
    """Image फाइल पढेर विश्लेषण गर्नुहोस्"""
    if not _is_path_allowed(file_path):
        return f"❌ Access denied: {file_path}"
    if not os.path.exists(file_path):
        return f"File not found: {file_path}"
    try:
        from image_analyzer import analyze_image
        result = analyze_image(file_path, question=question)
        return str(result)[:3000]
    except Exception as e:
        return f"❌ Image error: {e}"    
    
def tool_google_sheets_write(title: str, data_json: str) -> str:
    """नयाँ Google Sheet बनाएर data लेख्ने (data_json = list of dicts)"""
    import pandas as pd
    try:
        data = json.loads(data_json)
        df = pd.DataFrame(data)
        info = create_spreadsheet(title)
        write_dataframe_to_sheet(info["id"], df)
        return f"✅ Sheet created: {info['url']}"
    except Exception as e:
        return f"❌ Sheets error: {e}"


def tool_google_drive_upload(local_path: str) -> str:
    """लोकल फाइल Drive मा अपलोड गर्ने"""
    if not _is_path_allowed(local_path):
        return f"❌ Access denied: {local_path}"
    try:
        info = upload_file_to_drive(local_path)
        return f"✅ Uploaded: {info['url']}"
    except Exception as e:
        return f"❌ Drive error: {e}"


def tool_google_drive_search(query: str) -> str:
    """Drive मा फाइल खोज्ने"""
    try:
        files = list_drive_files(query=f"name contains '{query}' and trashed=false")
        if not files:
            return "कुनै फाइल भेटिएन।"
        return "\n".join([f"📄 {f['name']} → {f['webViewLink']}" for f in files[:10]])
    except Exception as e:
        return f"❌ Search error: {e}"    
    

def tool_send_message(friend_name: str, message: str):
    user_data = get_user_data(st.session_state.user)
    if friend_name not in user_data["friends"]:
        return f"Error: {friend_name} is not in your friend list."
    send_dm_db(st.session_state.user, friend_name, text=message)
    return f"✅ Message successfully sent to {friend_name}."

def tool_send_email(to_email: str, subject: str, body: str, attachment_path: str = "") -> str:
    try:
        ok = send_email_with_attachment(to_email, subject, body, attachment_path or None)
        if ok:
            log_action(st.session_state.user, "SEND_EMAIL", to_email, "success")   # ✅ नयाँ
            return f"✅ Email sent to {to_email}"
        log_action(st.session_state.user, "SEND_EMAIL", to_email, "failed")        # ✅ नयाँ
        return f"❌ Email failed to {to_email}"
    except Exception as e:
        log_action(st.session_state.user, "SEND_EMAIL", to_email, "error", str(e))  # ✅ नयाँ
        return f"❌ Email error: {e}"
    
def parse_table_from_text(text):
    try:
        from io import StringIO
        df = pd.read_csv(StringIO(text), sep=None, engine='python')
        if not df.empty: return df
    except Exception: pass
    try:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        data = []
        for line in lines:
            if '|' in line: parts = [p.strip() for p in line.split('|') if p.strip()]
            elif ',' in line: parts = [p.strip() for p in line.split(',')]
            elif '\t' in line: parts = [p.strip() for p in line.split('\t')]
            else: parts = [line]
            data.append(parts)
        max_cols = max(len(row) for row in data) if data else 0
        padded_data = [row + [''] * (max_cols - len(row)) for row in data]
        if len(padded_data) > 1:
            header = padded_data[0]
            df = pd.DataFrame(padded_data[1:], columns=header)
        else:
            df = pd.DataFrame(padded_data)
        return df
    except Exception as e:
        return None

# एजेन्टले प्रयोग गर्ने सबै उपकरण
AGENT_TOOLS_V2 = [
    tool_search_files,
    tool_read_any_file,
    tool_send_message,
    tool_write_file,
    tool_run_python,
    tool_list_directory,
    tool_summarize_pdf,
    tool_send_email,
    tool_google_sheets_write,     # ✅ नयाँ
    tool_google_drive_upload,     # ✅ नयाँ
    tool_google_drive_search,
    tool_analyze_image,
    #tool_send_whatsapp,
    tool_web_search,
    tool_read_webpage
]

# ============================================================
# Session State
# ============================================================
if "ui_lang" not in st.session_state: st.session_state.ui_lang = "ne"
if "active_chat_id" not in st.session_state: st.session_state.active_chat_id = str(uuid.uuid4())
if "active_doc_id" not in st.session_state: st.session_state.active_doc_id = str(uuid.uuid4())
if "active_img_id" not in st.session_state: st.session_state.active_img_id = str(uuid.uuid4())
if "active_table_id" not in st.session_state: st.session_state.active_table_id = str(uuid.uuid4())
if "show_friends_window" not in st.session_state: st.session_state.show_friends_window = False
if "dm_target" not in st.session_state: st.session_state.dm_target = None
if "search_user" not in st.session_state: st.session_state.search_user = ""
if "agent_result" not in st.session_state: st.session_state.agent_result = ""

defaults = {
    "messages": [], "voice_text": "", "extracted_tables": None, "extracted_pdf": "", 
    "auto_speak": False, "voice_lang": "ne-NP", "tts_lang": "ne", "last_audio_id": None, 
    "last_docs_audio_id": 0, "last_img_audio_id": 0, "last_table_audio_id": 0, "tag_filter": [], 
    "img_result": "", "img_path_saved": "", "img_name_saved": "", "pending_question": "", 
    "processing": False, "mini_doc_q": "", "mini_doc_a": "", "mini_doc_q_asked": "", 
    "mini_doc_input_version": 0, "mini_img_q": "", "mini_img_a": "", "mini_img_q_asked": "", 
    "mini_img_input_version": 0, "mini_table_q": "", "mini_table_a": "", "mini_table_q_asked": "", 
    "mini_table_input_version": 0, "ai_report_result": "", "feedback_given": set(),
    "edited_df": None, "forensic_result": "", "forensic_img_result": "",
    "local_path_to_read": "", "force_inbox": False
}
for key, val in defaults.items():
    if key not in st.session_state: st.session_state[key] = val

lang = st.session_state.ui_lang

# ============================================================
# AI Response Logic for Chat Window
# ============================================================
if st.session_state.get("pending_question"):
    question = st.session_state.pending_question
    st.session_state.processing = True
    st.session_state.messages.append({"role": "user", "content": question})
    
    memory_ctx = get_memory_context(st.session_state.user)
    if memory_ctx:
        question = f"{question}\n\n[User Memory: {memory_ctx}]"
    
    time.sleep(1) 
    full_answer = ""
    try:
        for chunk in stream_pdf_answer(question, st.session_state.user, target_lang=lang):
            full_answer += chunk
    except Exception as e:
        full_answer = f"❌ Error: {e}"
    
    st.session_state.messages.append({"role": "assistant", "content": full_answer})
    add_to_history(st.session_state.user, "chat", st.session_state.active_chat_id, question, st.session_state.messages)
    st.session_state.pending_question = ""
    st.session_state.processing = False
    st.rerun()

# ============================================================
# MESSENGER CALLBACKS (Single, Error-Free, Dialog-Safe)
# ============================================================
def _set_dm_target(target_name):
    """साथी वा AI च्याट खोल्न"""
    st.session_state.dm_target = target_name
    st.session_state.force_inbox = False

def _back_to_inbox():
    """इनबक्समा फर्कन"""
    st.session_state.dm_target = None
    st.session_state.force_inbox = True

def _accept_friend(req_user):
    """साथी अनुरोध स्वीकार"""
    accept_friend_request(st.session_state.user, req_user)
    st.session_state["_msg_flash"] = ("success", f"✅ {req_user} अब साथी बन्यो!")
    st.rerun()

def _reject_friend(req_user):
    """साथी अनुरोध अस्वीकार"""
    current = st.session_state.user
    data = get_user_data(current)
    if req_user in data["requests"]:
        data["requests"].remove(req_user)
        update_user_data(current, data["friends"], data["requests"])
    st.session_state["_msg_flash"] = ("info", f"❌ {req_user} को अनुरोध अस्वीकार गरियो")
    st.rerun()

def _send_friend_req(to_user):
    """साथी अनुरोध पठाउन"""
    ok = send_friend_request(st.session_state.user, to_user)
    if ok:
        st.session_state["_msg_flash"] = ("success", f"✅ Request sent to {to_user}!")
    else:
        st.session_state["_msg_flash"] = ("warning", f"⚠️ Request already sent to {to_user}")
    st.rerun()  # ✅ dialog रिफ्रेस गर्न अनिवार्य

def _send_file_cb(target, file_name, file_path):
    """फाइल पठाउन"""
    send_dm_db(st.session_state.user, target, text="", file_name=file_name, file_path=file_path)
    st.session_state["_msg_flash"] = ("success", "✅ File sent!")
    st.rerun()


# ============================================================
# MESSENGER WINDOW (Powerful, Error-Free, Callback-Based)
# ============================================================
@st.dialog("💬 Messenger", width="small")
def messenger_window():
    current_user = st.session_state.user
    target = st.session_state.get("dm_target")
    user_data = get_user_data(current_user)

    # --- FORCE INBOX RESET ---
    if st.session_state.get("force_inbox"):
        st.session_state.dm_target = None
        st.session_state.force_inbox = False
        target = None

    # ============================================================
    # 📥 INBOX VIEW
    # ============================================================
    if not target:
        update_last_read(current_user)

        search_query = st.text_input(
            "🔍 " + t("search", lang),
            value=st.session_state.search_user,
            key="search_input",
            label_visibility="collapsed",
            placeholder=t("search", lang)
        )
        st.session_state.search_user = search_query

        # ---------- CHAT LIST ----------
        st.markdown("### 💬 Chats")
        st.button(
            "🧠 PDF Brain AI",
            use_container_width=True,
            key="open_ai_chat",
            on_click=_set_dm_target,
            args=("PDF Brain AI",)
        )

        if not user_data["friends"]:
            st.caption("No friends yet.")
        else:
            for f in user_data["friends"]:
                if search_query.lower() in f.lower():
                    st.button(
                        f"👤 {f}",
                        key=f"chat_friend_{f}",
                        use_container_width=True,
                        on_click=_set_dm_target,
                        args=(f,)
                    )

        st.markdown("---")

        # ---------- FRIEND REQUESTS ----------
        req_count = len(user_data["requests"])
        req_title = "### 📩 Friend Requests" + (f" (🔴 {req_count})" if req_count > 0 else "")
        st.markdown(req_title)

        if req_count == 0:
            st.caption("No pending requests.")
        else:
            for req_user in user_data["requests"]:
                if search_query.lower() in req_user.lower():
                    st.markdown(f"**{req_user}** wants to be your friend.")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.button(
                            f"✅ {t('accept', lang)}",
                            key=f"acc_{req_user}",
                            use_container_width=True,
                            on_click=_accept_friend,
                            args=(req_user,)
                        )
                    with c2:
                        st.button(
                            f"❌ {t('reject', lang)}",
                            key=f"rej_{req_user}",
                            use_container_width=True,
                            on_click=_reject_friend,
                            args=(req_user,)
                        )

        st.markdown("---")

        # ---------- ADD FRIEND ----------
        st.markdown("### ➕ Add Friend")
        all_users = [u for u in get_all_users() if u != current_user]
        found_users = [
            u for u in all_users
            if search_query.lower() in u.lower()
            and u not in user_data["friends"]
            and u not in user_data["requests"]
        ]

        if not found_users:
            st.caption("No other users found.")
        else:
            for u in found_users:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"👤 **{u}**")
                with col2:
                    st.button(
                        "➕ Add",
                        key=f"add_friend_{u}",
                        use_container_width=True,
                        on_click=_send_friend_req,
                        args=(u,)
                    )

    # ============================================================
    # 💬 CHAT VIEW
    # ============================================================
    else:
        # ---------- Header ----------
        st.markdown(f"""
        <div class="messenger-header">
            <div class="avatar-circle">
                👤
                <div class="online-dot"></div>
            </div>
            <div>
                <h4 style="margin: 0; font-size: 1em; color: #050505;">{target}</h4>
                <p style="margin: 0; font-size: 0.8em; color: #31a24c;">🟢 {t("online", lang)}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ---------- Messages ----------
        chat_container = st.container(height=300)
        with chat_container:
            if target == "PDF Brain AI":
                msgs = st.session_state.messages
            else:
                msgs = get_dm_history_db(current_user, target)

            if not msgs:
                st.markdown(
                    f'<div style="text-align:center; color:#888; padding:20px;">'
                    f'Say Hi to {target}! 👋</div>',
                    unsafe_allow_html=True
                )

            for msg in msgs:
                if target == "PDF Brain AI":
                    role = msg["role"]
                    text = msg["content"]
                    f_name = None
                    f_path = None
                else:
                    role = "user" if msg["sender"] == current_user else "ai"
                    text = msg.get("message", "")
                    f_name = msg.get("file_name")
                    f_path = msg.get("file_path")

                if role == "user":
                    st.markdown(f'<div class="msg-bubble msg-user">{text}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="msg-bubble msg-ai">{text}</div>', unsafe_allow_html=True)

                if f_name and f_path and os.path.exists(f_path):
                    with open(f_path, "rb") as file:
                        st.download_button(
                            label=f"⬇️ {f_name}",
                            data=file,
                            file_name=f_name,
                            key=f"dl_{msg.get('timestamp')}_{f_name}"
                        )

            # ---------- Typing Indicator ----------
            if st.session_state.get("processing") and target == "PDF Brain AI":
                st.markdown(
                    '<div class="typing-indicator"><span></span><span></span><span></span></div>',
                    unsafe_allow_html=True
                )

        # ---------- File Upload ----------
        with st.expander(t("file_upload_label", lang)):
            uploaded_file = st.file_uploader(
                "Select File",
                key=f"file_uploader_{target}"
            )
            if uploaded_file:
                os.makedirs(UPLOAD_DIR, exist_ok=True)
                saved_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
                with open(saved_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.button(
                    t("send_file", lang),
                    key=f"send_file_btn_{target}",
                    use_container_width=True,
                    on_click=_send_file_cb,
                    args=(target, uploaded_file.name, saved_path)
                )

        # ---------- Chat Input ----------
        prompt = st.chat_input(
            t("type_msg", lang),
            key=f"messenger_chat_input_{target}"
        )
        if prompt:
            if target == "PDF Brain AI":
                st.session_state.pending_question = prompt
            else:
                send_dm_db(current_user, target, text=prompt)
            st.rerun()

        # ---------- Back Button ----------
        st.button(
            t("back_to_chats", lang),
            use_container_width=True,
            key=f"back_btn_{target}",
            on_click=_back_to_inbox
        )


# ============================================================
# SIDEBAR — DeepSeek Style (Powerful & Stable)
# ============================================================
with st.sidebar:
    # ============================================================
    # 👤 1. USER PROFILE CARD (Avatar + Logout)
    # ============================================================
    avatar_html = render_avatar(st.session_state.user, size=50)

    st.markdown(f"""
    <div class="fb-profile-card">
        <div class="fb-row">
            <div class="fb-avatar-wrap">
                {avatar_html}
                <div class="fb-online-dot"></div>
            </div>
            <div class="fb-info">
                <h4>{st.session_state.user}</h4>
                <p>🟢 Online <span class="fb-role-badge">{st.session_state.get('user_role', 'user').upper()}</span></p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---- Profile + Logout buttons (side by side) ----
    prof_col1, prof_col2 = st.columns(2)

    with prof_col1:
        # Profile Photo (popover)
        with st.popover("📷 Photo", use_container_width=True):
            st.markdown(f"""
            <div style="text-align:center; padding: 8px 0;">
                {render_avatar(st.session_state.user, size=80)}
            </div>
            """, unsafe_allow_html=True)

            avatar_file = st.file_uploader(
                "Choose new photo",
                type=["png", "jpg", "jpeg", "webp"],
                key="avatar_upload",
                label_visibility="collapsed"
            )
            if avatar_file:
                if st.button("💾 Save", key="save_avatar_btn", use_container_width=True):
                    save_avatar(st.session_state.user, avatar_file)
                    st.success("✅ Saved!")
                    st.rerun()

            if get_avatar_path(st.session_state.user):
                if st.button("🗑️ Remove", key="remove_avatar_btn", use_container_width=True):
                    os.remove(get_avatar_path(st.session_state.user))
                    st.rerun()

    with prof_col2:
        # ✅ Logout (भरपर्दो — st.button)
        if st.button("🚪 Logout", key="logout_btn_final", use_container_width=True):
            # Audit
            if st.session_state.get("user"):
                log_action(st.session_state.user, "LOGOUT", status="success")
                
                # ✅ Flag reset (user None हुनु अघि)
            st.session_state.logged_in = False
            
            # सबै session_state सफा
            for key in list(st.session_state.keys()):
                if key not in ["ui_lang"]:
                    del st.session_state[key]
            st.session_state.user = None
            st.rerun()

    st.markdown("---")
    
    # ✅ नयाँ: User Dashboard
    from user_stats import get_user_dashboard_stats
    st.markdown("---")
    st.markdown("### 📊 तपाईंको प्रगति")
    u_stats = get_user_dashboard_stats(st.session_state.user)
    st.metric("📄 PDF हरू", u_stats["pdfs"])
    st.metric("💬 च्याटहरू", u_stats["chats"])
    st.metric("📊 टेबलहरू", u_stats["tables"])
    st.metric("🤖 एजेन्ट रन", u_stats["agent_runs"])

    # ============================================================
    # 💬 2. MESSENGER ICON
    # ============================================================
    current_user_data = get_user_data(st.session_state.user)
    unread_msgs, unread_reqs = get_unread_count(st.session_state.user, current_user_data)
    total_notifs = unread_msgs + unread_reqs

    st.markdown('<div class="messenger-icon-wrap">', unsafe_allow_html=True)
    if total_notifs > 0:
        st.markdown(f'<span class="messenger-badge">{total_notifs}</span>', unsafe_allow_html=True)
    if st.button("💬", key="sidebar_messenger_btn", help=t("messenger", lang)):
        st.session_state.show_friends_window = True
        st.session_state.force_inbox = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ============================================================
    # 🔍 3. SEARCH BAR (Ctrl+K)
    # ============================================================
    search_query = st.text_input(
        "🔍 Search...",
        placeholder="Search... (Ctrl+K)",
        key="ds_search",
        label_visibility="collapsed"
    )

    # ============================================================
    # 🧠 4. MEMORY PANEL
    # ============================================================
    memories = get_memories(st.session_state.user, limit=15)
    mem_count = len(memories)
    st.markdown(f"""
    <div class="memory-header">
        <span>🧠</span>
        <span>Memory</span>
        <span class="count">{mem_count}</span>
    </div>
    """, unsafe_allow_html=True)

    if not memories:
        st.markdown("""
        <div class="memory-empty">
            कुनै memory छैन<br>
            <span style="font-size:0.85em;">कुराकानी गर्दा स्वतः बन्छ</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        type_labels = {"fact": "तथ्य", "preference": "रुचि", "summary": "सारांश", "profile": "प्रोफाइल"}
        emoji_map = {"fact": "📌", "preference": "⚙️", "summary": "📝", "profile": "👤"}

        for m in memories:
            if search_query and search_query.lower() not in m["content"].lower():
                continue
            emoji = emoji_map.get(m["memory_type"], "•")
            type_label = type_labels.get(m["memory_type"], m["memory_type"])
            content_safe = m["content"].replace("<", "&lt;").replace(">", "&gt;")

            col_a, col_b = st.columns([8, 1])
            with col_a:
                st.markdown(f"""
                <div class="memory-item">
                    <span class="m-icon">{emoji}</span>
                    <div class="m-text">
                        {content_safe}
                        <span class="m-type">{type_label} · {m.get('importance', 5)}/10</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                if st.button("🗑️", key=f"del_mem_{m['id']}", help="मेटाउनुहोस्"):
                    delete_memory(st.session_state.user, m["id"])
                    st.rerun()

    if mem_count > 0:
        if st.button("🗑️ सबै Memory मेटाउनुहोस्", key="clear_all_mem", use_container_width=True):
            clear_all_memories(st.session_state.user)
            st.rerun()

    st.markdown("---")

    # ============================================================
    # 📚 5. HISTORY (Tabs)
    # ============================================================
    user_history = load_history(st.session_state.user)
    st.markdown('<div class="ds-section">📚 History</div>', unsafe_allow_html=True)

    hist_tab1, hist_tab2, hist_tab3, hist_tab4 = st.tabs(["💬", "📄", "🖼️", "📊"])

    with hist_tab1:
        if user_history.get("chat"):
            for cid, cdata in sorted(user_history["chat"].items(), key=lambda x: x[1]["timestamp"], reverse=True)[:5]:
                if search_query and search_query.lower() not in cdata["title"].lower():
                    continue
                col1, col2 = st.columns([5, 1])
                with col1:
                    if st.button(f"💬 {cdata['title'][:18]}...", key=f"sb_chat_{cid}", use_container_width=True):
                        st.session_state.active_chat_id = cid
                        st.session_state.messages = cdata["data"]
                        st.session_state.dm_target = "PDF Brain AI"
                        st.session_state.force_inbox = False
                        st.session_state.show_friends_window = True
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_chat_{cid}"):
                        delete_history_item(st.session_state.user, "chat", cid)
                        st.rerun()
        else:
            st.markdown('<div class="ds-empty">कुनै च्याट छैन</div>', unsafe_allow_html=True)

    with hist_tab2:
        if user_history.get("docs"):
            for did, ddata in sorted(user_history["docs"].items(), key=lambda x: x[1]["timestamp"], reverse=True)[:5]:
                if search_query and search_query.lower() not in ddata["title"].lower():
                    continue
                col1, col2 = st.columns([5, 1])
                with col1:
                    if st.button(f"📄 {ddata['title'][:18]}...", key=f"dc_{did}", use_container_width=True):
                        st.session_state.active_doc_id = did
                        st.session_state.mini_doc_q = ddata.get("extra_state", {}).get("q", "")
                        st.session_state.mini_doc_a = ddata["data"]
                        st.session_state.mini_doc_q_asked = ddata.get("extra_state", {}).get("q", "")
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"ddc_{did}"):
                        delete_history_item(st.session_state.user, "docs", did)
                        st.rerun()
        else:
            st.markdown('<div class="ds-empty">कुनै PDF छैन</div>', unsafe_allow_html=True)

    with hist_tab3:
        if user_history.get("image"):
            for iid, idata in sorted(user_history["image"].items(), key=lambda x: x[1]["timestamp"], reverse=True)[:5]:
                if search_query and search_query.lower() not in idata["title"].lower():
                    continue
                col1, col2 = st.columns([5, 1])
                with col1:
                    if st.button(f"🖼️ {idata['title'][:18]}...", key=f"im_{iid}", use_container_width=True):
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
        else:
            st.markdown('<div class="ds-empty">कुनै Image छैन</div>', unsafe_allow_html=True)

    with hist_tab4:
        if user_history.get("table"):
            for tid, tdata in sorted(user_history["table"].items(), key=lambda x: x[1]["timestamp"], reverse=True)[:5]:
                if search_query and search_query.lower() not in tdata["title"].lower():
                    continue
                col1, col2 = st.columns([5, 1])
                with col1:
                    if st.button(f"📊 {tdata['title'][:18]}...", key=f"tb_{tid}", use_container_width=True):
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
        else:
            st.markdown('<div class="ds-empty">कुनै Table छैन</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ============================================================
    # ⚙️ 6. SETTINGS (एउटै expander भित्र)
    # ============================================================
    st.markdown('<div class="ds-section">⚙️ Settings</div>', unsafe_allow_html=True)

    with st.expander("⚙️ Settings", expanded=False):
        # 🌐 Language
        st.markdown("##### 🌐 Language")
        ui_lang_map = {"🇳🇵 नेपाली": "ne", "🇬🇧 English": "en", "🇮🇳 हिन्दी": "hi"}
        ui_keys = list(ui_lang_map.keys())
        ui_values = list(ui_lang_map.values())
        current_index = ui_values.index(lang) if lang in ui_values else 0
        selected_ui = st.selectbox(
            "UI Language", ui_keys, index=current_index,
            key="ui_lang_select", label_visibility="collapsed"
        )
        new_lang = ui_lang_map[selected_ui]
        if new_lang != lang:
            st.session_state.ui_lang = new_lang
            st.rerun()

        st.markdown("---")

        # 🎤 Voice
        st.markdown("##### 🎤 Voice")
        st.session_state.auto_speak = st.toggle(
            t("auto_speak", lang),
            value=st.session_state.auto_speak,
            key="ds_auto_speak"
        )
        voice_lang_map = {"नेपाली": "ne-NP", "English": "en-US", "हिन्दी": "hi-IN"}
        voice_label = st.selectbox(
            t("input_lang", lang),
            list(voice_lang_map.keys()),
            index=0,
            key="v_lang_in_ds"
        )
        st.session_state.voice_lang = voice_lang_map[voice_label]
        tts_lang_map = {"नेपाली": "ne", "English": "en", "हिन्दी": "hi"}
        tts_label = st.selectbox(
            t("output_lang", lang),
            list(tts_lang_map.keys()),
            index=0,
            key="v_lang_out_ds"
        )
        st.session_state.tts_lang = tts_lang_map[tts_label]

        st.markdown("---")

        # 🔔 Notifications
        st.markdown("##### 🔔 Notifications")
        st.session_state.show_notifications = st.toggle(
            "Desktop Notifications",
            value=st.session_state.get("show_notifications", True),
            key="ds_notif"
        )
        st.caption("नयाँ message/report को सूचना")

        st.markdown("---")

        # 🌙 Appearance
        st.markdown("##### 🌙 Appearance")
        dark_mode = st.toggle(
            "Dark Mode",
            value=st.session_state.get("dark_mode", False),
            key="ds_dark_mode_toggle"
        )
        if dark_mode != st.session_state.get("dark_mode"):
            st.session_state.dark_mode = dark_mode
            st.rerun()

    st.markdown("---")

    # ============================================================
    # 🎯 7. FOOTER
    # ============================================================
    st.markdown(f"""
    <div class="ds-footer">
        <div class="ds-version">🧠 PDF Brain v52.0</div>
        <div class="ds-links">
            <a href="#">Help</a>
            <a href="#">Privacy</a>
            <a href="#">About</a>
        </div>
        <div style="font-size:0.65em; color:#8892b0;">Made with ❤️ in Nepal</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# OPEN WINDOWS
# ============================================================
if st.session_state.get("show_friends_window"):
    messenger_window()
    st.session_state.show_friends_window = False
    
# ============================================================
# FLASH MESSAGES (callback पछि प्रदर्शन)
# ============================================================
if "_msg_flash" in st.session_state:
    flash_type, flash_text = st.session_state.pop("_msg_flash")
    if flash_type == "success":
        st.success(flash_text)
    elif flash_type == "warning":
        st.warning(flash_text)
    elif flash_type == "info":
        st.info(flash_text)
    else:
        st.toast(flash_text)    

# ============================================================
# MAIN AREA (Tabs)
# ============================================================
render_sticky_header(st.session_state.user, lang)

# ============================================================
# TABS (Admin + Video)
# ============================================================
is_admin = st.session_state.get("user_role", "user") == "admin"

if is_admin:
    tab1, tab2, tab3, tab4, tab_video, tab_caption, tab_crm, tab_admin = st.tabs([
        t("docs_tab", lang), t("image_tab", lang), t("table_tab", lang),
        t("agent_tab", lang), "🎬 HD Converter", "💬 Auto Caption", "💼 Client Manager", "👑 Admin Dashboard"
    ])
else:
    tab1, tab2, tab3, tab4, tab_video, tab_caption, tab_crm = st.tabs([
        t("docs_tab", lang), t("image_tab", lang), t("table_tab", lang),
        t("agent_tab", lang), "🎬 HD Converter", "💬 Auto Caption", "💼 Client Manager"
    ])
    tab_admin = None
    
# ============================================================
# TAB 1: DOCUMENTS
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
        st.caption(t("upload_hint", lang) + " " + t("multi_upload_hint", lang))
        
        uploaded_files = st.file_uploader(t("upload_doc", lang), type=["pdf", "docx", "doc", "txt", "md", "jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key="user_doc_upload", label_visibility="collapsed")
        
        if uploaded_files:
            if st.button(t("upload_process", lang), use_container_width=True, type="primary", key="docs_upload_process"):
                uploaded_count = 0
                with st.spinner(t("uploading", lang)):
                    for file in uploaded_files:
                        try:
                            save_user_pdf(st.session_state.user, file.getbuffer(), file.name); uploaded_count += 1
                            log_action(st.session_state.user, "UPLOAD_DOC", file.name, "success")   # ✅ नयाँ
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
                
                memory_ctx = get_memory_context(st.session_state.user)
                doc_q_with_mem = f"{mini_doc_q}\n\n[User Memory: {memory_ctx}]" if memory_ctx else mini_doc_q
                    
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
                
                with st.expander(f"📤 {t('share_btn', lang)}"):
                    user_data = get_user_data(st.session_state.user)
                    friends_list = user_data.get("friends", [])
                    if friends_list:
                        selected_friends = st.multiselect(t("team_share", lang), friends_list, key="doc_multi_share")
                        if st.button(t("send_to_messenger", lang), key="doc_send_btn"):
                            if selected_friends:
                                for f in selected_friends: send_dm_db(st.session_state.user, f, text=st.session_state.mini_doc_a)
                                st.success(t("send_success", lang))
                            else: st.warning("Select at least one friend.")
                    else: st.warning("No friends to share with.")
        else: st.info(t("no_files", lang))
    except ImportError: st.error("⚠️ user_manager.py भेटिएन")

# ============================================================
# TAB 2: IMAGE
# ============================================================
with tab2:
    st.markdown(f"### {t('image_analysis', lang)}")
    st.caption(t("image_hint", lang) + " " + t("multi_upload_hint", lang))
    col1, col2 = st.columns([1, 1])
    with col1:
        uploaded_images = st.file_uploader(t("upload_image", lang), type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key="img_upload_tab", label_visibility="collapsed")
        
        if uploaded_images:
            st.write(f"**{len(uploaded_images)} image(s) selected.**")
            cols = st.columns(4)
            for i, img in enumerate(uploaded_images):
                with cols[i % 4]: st.image(img, width=100)
            
            if st.button(t("analyze_btn", lang), use_container_width=True, type="primary", key="img_analyze_btn"):
                os.makedirs("temp_images", exist_ok=True)
                results = []
                with st.spinner(t("analyzing", lang)):
                    from image_analyzer import analyze_image
                    for img in uploaded_images:
                        img_path = os.path.join("temp_images", img.name)
                        with open(img_path, "wb") as f: f.write(img.getbuffer())
                        try:
                            result = analyze_image(img_path)
                            results.append(f"### 📸 {img.name}\n{result}\n\n---\n")
                        except Exception as e:
                            results.append(f"### 📸 {img.name}\n❌ Error: {e}\n\n---\n")
                
                st.session_state.img_result = "\n".join(results)
                st.session_state.img_path_saved = os.path.join("temp_images", uploaded_images[0].name)
                st.session_state.img_name_saved = uploaded_images[0].name
                st.rerun()

        if st.session_state.get("img_path_saved") and os.path.exists(st.session_state.img_path_saved):
            st.markdown("---")
            if st.button(t("delete_btn", lang), use_container_width=True, key="img_delete_btn"):
                if os.path.exists(st.session_state.img_path_saved):
                    try: os.remove(st.session_state.img_path_saved)
                    except Exception: pass
                st.session_state.img_path_saved = ""; st.session_state.img_name_saved = ""; st.session_state.img_result = ""; st.session_state.mini_img_a = ""; st.rerun()
    
    with col2:
        st.markdown(f"#### {t('result', lang)}")
        if st.session_state.get("img_result"): 
            st.markdown(st.session_state.img_result)
            
            st.markdown("---")
            st.markdown(f"#### {t('forensic_result', lang)}")
            st.caption(t("forensic_hint", lang))
            if st.button(t("forensic_btn", lang), key="forensic_img_btn", use_container_width=True, type="primary"):
                with st.spinner(t("forensic_analyzing", lang)):
                    st.session_state.forensic_img_result = forensic_check(file_type="image", file_path=st.session_state.img_path_saved, lang=lang)
            
            if st.session_state.get("forensic_img_result"):
                st.markdown(f'<div class="chat-a-box">🕵️‍♂️ {st.session_state.forensic_img_result}</div>', unsafe_allow_html=True)
            
            with st.expander(f"📤 {t('share_btn', lang)} (Analysis)"):
                user_data = get_user_data(st.session_state.user)
                friends_list = user_data.get("friends", [])
                if friends_list:
                    selected_friends = st.multiselect(t("team_share", lang), friends_list, key="auto_img_share")
                    if st.button(t("send_to_messenger", lang), key="auto_img_send_btn"):
                        if selected_friends:
                            for f in selected_friends: send_dm_db(st.session_state.user, f, text=st.session_state.img_result)
                            st.success(t("send_success", lang))
                        else: st.warning("Select at least one friend.")
                else: st.warning("No friends to share with.")
        else: 
            st.markdown(f'<div class="empty-state"><div class="icon">🖼️</div><p>{t("upload_prompt", lang)}</p></div>', unsafe_allow_html=True)

# ============================================================
# TAB 3: TABLE + CHART
# ============================================================
with tab3:
    st.markdown(f"### {t('table_chart', lang)}")
    st.caption(t("table_hint", lang) + " " + t("multi_upload_hint", lang))
    
    source_option = st.radio(t("where_extract", lang), [t("upload_new_file", lang), t("select_from_docs", lang)], horizontal=True, label_visibility="collapsed")
    
    tables = None
    file_display_name = ""
    
    if source_option == t("upload_new_file", lang):
        uploaded_table_files = st.file_uploader(t("upload_file_label", lang), type=["pdf", "xlsx", "xls", "csv", "jpg", "jpeg", "png"], accept_multiple_files=True, key="table_file_uploader")
        
        if uploaded_table_files:
            st.write(f"**{len(uploaded_table_files)} file(s) selected.**")
            if st.button(t("extract_tables_btn", lang), use_container_width=True, type="primary", key="extract_from_upload"):
                os.makedirs("temp_tables", exist_ok=True)
                all_tables = []
                with st.spinner(t("extracting", lang)):
                    for uploaded_table_file in uploaded_table_files:
                        try:
                            temp_path = os.path.join("temp_tables", uploaded_table_file.name)
                            with open(temp_path, "wb") as f: f.write(uploaded_table_file.getbuffer())
                            
                            file_ext = uploaded_table_file.name.lower().split(".")[-1]
                            file_display_name = uploaded_table_file.name
                            
                            if file_ext == "pdf":
                                from table_extractor import extract_tables
                                tables = extract_tables(temp_path)
                                if tables: all_tables.extend(tables)
                            elif file_ext in ["xlsx", "xls"]:
                                xls = pd.ExcelFile(temp_path)
                                for sheet_name in xls.sheet_names:
                                    df = pd.read_excel(xls, sheet_name=sheet_name)
                                    all_tables.append({"page": 1, "index": f"{uploaded_table_file.name} ({sheet_name})", "dataframe": df, "rows": len(df), "cols": len(df.columns)})
                            elif file_ext == "csv":
                                df = pd.read_csv(temp_path)
                                all_tables.append({"page": 1, "index": uploaded_table_file.name, "dataframe": df, "rows": len(df), "cols": len(df.columns)})
                            elif file_ext in ["jpg", "jpeg", "png"]:
                                from image_analyzer import analyze_image
                                result_text = analyze_image(temp_path, question="Extract all data from this table. Return ONLY a valid CSV format. No explanation, no markdown code blocks, just plain CSV text with headers.")
                                df = parse_table_from_text(result_text)
                                if df is not None and not df.empty:
                                    all_tables.append({"page": 1, "index": uploaded_table_file.name, "dataframe": df, "rows": len(df), "cols": len(df.columns)})
                                else:
                                    st.warning(f"Could not parse table from image: {uploaded_table_file.name}")
                                    st.text(result_text)
                        except Exception as e: st.error(f"❌ Error processing {uploaded_table_file.name}: {e}")
                
                if all_tables:
                    st.session_state.extracted_tables = all_tables
                    st.session_state.extracted_pdf = "Multiple Files"
                    add_to_history(st.session_state.user, "table", st.session_state.active_table_id, "Multiple Files", "Extracted", 
                                   {"pdf": "Multiple Files", "tables": [{"page": t["page"], "index": t["index"], "rows": t["rows"], "cols": t["cols"], "dataframe": t["dataframe"].to_dict(orient="records")} for t in all_tables]})
                    st.rerun()
                else: st.warning(t("no_table", lang))
    
    else:
        if os.path.exists("docs"):
            pdf_files = [f for f in os.listdir("docs") if f.lower().endswith((".pdf", ".xlsx", ".csv"))]
            if pdf_files:
                col1, col2 = st.columns([3, 1])
                with col1: selected_pdf = st.selectbox(t("pdf_select", lang), pdf_files, key="table_pdf_tab")
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
                                else: st.warning(t("no_table", lang))
                            except Exception as e: st.error(f"❌ {e}")
            else: st.info(t("no_pdf", lang))
        else: st.info(t("no_docs_folder", lang))

    if st.session_state.get("extracted_tables"):
        tables = st.session_state.extracted_tables
        st.success(f"✅ {len(tables)} {t('table_found_msg', lang)} {st.session_state.extracted_pdf}")
        
        from chart_maker import make_chart, get_summary_stats, df_to_csv_bytes
        
        for idx, tbl in enumerate(tables, 1):
            df = tbl["dataframe"].copy()
            with st.expander(f"📋 Table {idx} — {tbl['index']} ({tbl['rows']}×{tbl['cols']})", expanded=(idx == 1)):
                sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([t("data_tab", lang), t("chart_tab", lang), t("stats_tab", lang), "🤖 AI Report"])
                
                with sub_tab1:
                    st.caption(t("data_edit_hint", lang))
                    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", key=f"editor_{idx}")
                    st.session_state.extracted_tables[idx-1]["dataframe"] = edited_df
                    
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(t("download_excel", lang), df_to_excel_bytes(edited_df), file_name=f"table_{idx}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"xlsx_{idx}", use_container_width=True)
                    with col_dl2:
                        st.download_button(t("download_csv", lang), df_to_csv_bytes(edited_df), file_name=f"table_{idx}.csv", mime="text/csv", key=f"csv_{idx}", use_container_width=True)
                    
                    st.markdown("---")
                    st.markdown(f"#### {t('forensic_result', lang)}")
                    st.caption(t("forensic_hint", lang))
                    if st.button(t("forensic_btn", lang), key=f"forensic_table_btn_{idx}", use_container_width=True, type="primary"):
                        with st.spinner(t("forensic_analyzing", lang)):
                            st.session_state.forensic_result = forensic_check(file_type="table", data=edited_df, lang=lang)
                    
                    if st.session_state.get("forensic_result"):
                        st.markdown(f'<div class="chat-a-box">🕵️‍♂️ {st.session_state.forensic_result}</div>', unsafe_allow_html=True)
                        with st.expander(f"📤 {t('share_btn', lang)} (Forensic)"):
                            user_data = get_user_data(st.session_state.user)
                            friends_list = user_data.get("friends", [])
                            if friends_list:
                                selected_friends = st.multiselect(t("team_share", lang), friends_list, key=f"forensic_table_share_{idx}")
                                if st.button(t("send_to_messenger", lang), key=f"forensic_table_send_btn_{idx}"):
                                    if selected_friends:
                                        for f in selected_friends: send_dm_db(st.session_state.user, f, text=f"🕵️‍♂️ Forensic Report:\n{st.session_state.forensic_result}")
                                        st.success(t("send_success", lang))
                                    else: st.warning("Select at least one friend.")
                            else: st.warning("No friends to share with.")
                
                with sub_tab2:
                    numeric_cols = edited_df.select_dtypes(include=["number"]).columns.tolist()
                    if not numeric_cols:
                        for col in edited_df.columns:
                            edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(r'[$,]', '', regex=True), errors="coerce")
                        numeric_cols = edited_df.select_dtypes(include=["number"]).columns.tolist()
                    
                    if numeric_cols:
                        text_cols = [c for c in edited_df.columns if c not in numeric_cols]
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            x_default = text_cols[0] if text_cols else edited_df.columns[0]
                            x_index = edited_df.columns.tolist().index(x_default) if x_default in edited_df.columns.tolist() else 0
                            x_col = st.selectbox("X", edited_df.columns.tolist(), index=x_index, key=f"tab_x_{idx}")
                        with c2: y_col = st.selectbox("Y", numeric_cols, key=f"tab_y_{idx}")
                        with c3: chart_type = st.selectbox("Type", ["bar", "line", "pie", "area", "scatter"], key=f"tab_t_{idx}")
                        
                        fig = make_chart(edited_df, chart_type=chart_type, x_col=x_col, y_col=y_col)
                        if fig: st.plotly_chart(fig, use_container_width=True)
                    else: st.warning(t("no_numeric", lang))
                
                with sub_tab3:
                    stats = get_summary_stats(edited_df)
                    for col, s in stats.items():
                        st.markdown(f"**📊 {col}**")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric(t("sum", lang), f"{s['sum']:,.2f}"); c2.metric(t("avg", lang), f"{s['mean']:,.2f}"); c3.metric(t("min", lang), f"{s['min']:,.2f}"); c4.metric(t("max", lang), f"{s['max']:,.2f}")
                
                with sub_tab4:
                    st.markdown(f"#### {t('ai_report_title', lang)}")
                    st.caption(t("ai_report_desc", lang))
                    if st.button(t("ai_report_btn", lang), key=f"ai_report_{idx}", use_container_width=True, type="primary"):
                        with st.spinner("AI..."):
                            report = universal_answer("", context_type="ai_report", context_data=edited_df, target_lang=lang)
                            st.session_state.ai_report_result = report
                    
                    if st.session_state.get("ai_report_result"):
                        st.markdown(f'<div class="chat-a-box">{st.session_state.ai_report_result}</div>', unsafe_allow_html=True)
                        st.download_button(t("download_report", lang), st.session_state.ai_report_result, file_name=f"AI_Report_{idx}.txt", mime="text/plain", key=f"dl_report_{idx}")
                        
                        with st.expander(f"📤 {t('share_btn', lang)}"):
                            user_data = get_user_data(st.session_state.user)
                            friends_list = user_data.get("friends", [])
                            if friends_list:
                                selected_friends = st.multiselect(t("team_share", lang), friends_list, key=f"table_multi_share_{idx}")
                                if st.button(t("send_to_messenger", lang), key=f"table_send_btn_{idx}"):
                                    if selected_friends:
                                        for f in selected_friends: send_dm_db(st.session_state.user, f, text=st.session_state.ai_report_result)
                                        st.success(t("send_success", lang))
                                    else: st.warning("Select at least one friend.")
                            else: st.warning("No friends to share with.")
        
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
            mini_table_q = st.text_input(t("your_question", lang), value="", placeholder=t("table_placeholder", lang), key=input_key_table, label_visibility="collapsed")
        
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1: table_ask_clicked = st.button(t("ask_btn", lang), key="table_ask_btn", use_container_width=True, type="primary")
        with col_btn2:
            if st.button(t("clear_btn", lang), key="table_clear_btn", use_container_width=True):
                st.session_state.mini_table_q = ""; st.session_state.mini_table_a = ""
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
            if st.button(t("copy_answer", lang), key="copy_table_ans"): st.code(st.session_state.mini_table_a, language=None)

            
# ============================================================
# TAB 4: AUTO-PILOT AGENT (Powerful v2)
# ============================================================
with tab4:
    st.markdown(f"### {t('agent_tab', lang)}")
    st.caption("AI ले आफैंले काम गर्ने पावरफुल एजेन्ट। तपाईंले लक्ष्य दिनुहोस्, बाँकी AI ले गर्छ। (Local Files + Python + Write + Summarize)")

    # ---- Agent Config ----
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"#### {t('agent_goal', lang)}")
        goal = st.text_area(
            t("agent_goal", lang),
            placeholder=t("agent_goal_placeholder", lang),
            height=120,
            label_visibility="collapsed",
            key="agent_goal_v2"
        )
    with col2:
        st.markdown("#### ⚙️ Agent Settings")
        max_steps = st.slider("Max Steps", 5, 30, 15, key="agent_max_steps")
        show_logs = st.toggle("Show Work Logs", value=True, key="agent_show_logs")
        st.caption(f"🛠️ Tools: {len(AGENT_TOOLS_V2)} available")

    # ---- Allowed Folders Info ----
    with st.expander("🔒 Allowed Folders (Agent can only access these)"):
        for root in AGENT_ALLOWED_ROOTS:
            st.code(root, language=None)
        st.caption("Agent cannot read/write outside these folders. Edit AGENT_ALLOWED_ROOTS in code to change.")

    # ---- Run Agent ----
    if st.button(t("agent_run_btn", lang), type="primary", use_container_width=True, key="agent_run_v2"):
        if not goal.strip():
            st.warning("Please enter a goal.")
        else:
            logs = []
            final_answer = ""
            steps_taken = 0

            status_placeholder = st.empty()
            status_placeholder.info(f"🤖 {t('agent_working', lang)}")

            try:
                client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                chat = client.chats.create(
                    model="gemini-3.5-flash-lite",
                    config=types.GenerateContentConfig(
                        tools=AGENT_TOOLS_V2,
                        temperature=0.1,
                    )
                )

                # ✅ सुरुवाती सन्देश (Universal Multilingual Support)
                system_hint = (
                    f"You are a powerful autonomous agent. Your goal: {goal}\n\n"
                    f"🌍 LANGUAGE RULE:\n"
                    f"You MUST reply in the EXACT SAME LANGUAGE as the user's goal/request. "
                    f"(e.g., if the goal is in Spanish, reply in Spanish; if in Japanese, reply in Japanese; if in Nepali, reply in Nepali). "
                    f"Never translate the user's language to English unless requested.\n\n"
                    f"Rules:\n"
                    f"1. Break the goal into steps. Use tools to gather info, write files, run Python.\n"
                    f"2. Only access folders listed in AGENT_ALLOWED_ROOTS.\n"
                    f"3. If the goal asks for current data (price, news, weather, etc.), use **tool_web_search**.\n"
                    f"4. When showing web search results, **QUOTE THE EXACT NUMBERS** from the search result. Do not guess or approximate.\n"
                    f"5. If the goal asks to send an email, use **tool_send_email**.\n"
                    f"6. When done, give a clear final answer summarizing what you did.\n"
                    f"7. If a tool fails, try a different approach.\n"
                    f"8. Be concise but thorough.\n"
                    f"9. CRITICAL FOR WEB SEARCH: If the user asks for live data (price, news), first use **tool_web_search**. Then, use **tool_read_webpage** on the top 1 or 2 links to read the exact details before answering.\n"
                )
                response = chat.send_message(system_hint)

                # ---- Agent Loop ----
                while steps_taken < max_steps:
                    steps_taken += 1

                    if response.function_calls:
                        # Parallel tool calls support
                        function_responses = []
                        for tool_call in response.function_calls:
                            tool_name = tool_call.name
                            tool_args = dict(tool_call.args) if tool_call.args else {}
                            call_id = tool_call.id  # ✅ Tool response ID

                            logs.append(f"🔧 Step {steps_taken}: `{tool_name}` args={str(tool_args)[:200]}")

                            # Execute tool
                            if tool_name == "tool_search_files":
                                result = tool_search_files(**tool_args)
                            elif tool_name == "tool_read_any_file":
                                result = tool_read_any_file(**tool_args)
                            elif tool_name == "tool_send_message":
                                result = tool_send_message(**tool_args)
                            elif tool_name == "tool_write_file":
                                result = tool_write_file(**tool_args)
                            elif tool_name == "tool_run_python":
                                result = tool_run_python(**tool_args)
                            elif tool_name == "tool_list_directory":
                                result = tool_list_directory(**tool_args)
                            elif tool_name == "tool_summarize_pdf":
                                result = tool_summarize_pdf(**tool_args)
                            elif tool_name == "tool_send_email":
                                result = tool_send_email(**tool_args)
                            elif tool_name == "tool_google_sheets_write":
                                result = tool_google_sheets_write(**tool_args)
                            elif tool_name == "tool_google_drive_upload":
                                result = tool_google_drive_upload(**tool_args)
                            elif tool_name == "tool_google_drive_search":
                                result = tool_google_drive_search(**tool_args)
                            elif tool_name == "tool_web_search":
                                result = tool_web_search(**tool_args) 
                            elif tool_name == "tool_read_webpage":
                                result = tool_read_webpage(**tool_args)
                            else:
                                result = f"Unknown tool: {tool_name}"
                                
                            logs.append(f"   ↳ Result: {str(result)[:300]}")

                            # Function response with ID (context circulation)
                            function_responses.append(
                                types.Part.from_function_response(
                                    name=tool_name,
                                    response={"result": str(result)},
                                    #id=call_id  # ✅ ID सहित
                                )
                            )

                        # Send all tool results back
                        response = chat.send_message(function_responses)
                    else:
                        # No more tool calls — final answer
                        final_answer = response.text or "(no answer)"
                        logs.append(f"✅ Step {steps_taken}: Final answer generated.")
                        break

                if not final_answer:
                    final_answer = "⚠️ Agent reached max steps without final answer. Last state: " + str(response.text)[:500]

                status_placeholder.success(t("agent_success", lang))

                # ---- Output ----
                st.markdown(f'<div class="chat-a-box">{final_answer}</div>', unsafe_allow_html=True)

                if show_logs and logs:
                    with st.expander(f"📋 {t('agent_logs', lang)} ({len(logs)} entries)"):
                        for log in logs:
                            st.text(log)

                # ---- Save result to history ----
                add_to_history(
                    st.session_state.user, "chat",
                    st.session_state.active_chat_id,
                    f"Agent: {goal[:40]}",
                    st.session_state.messages,
                    {"agent_result": final_answer}
                )

            except Exception as e:
                status_placeholder.error(f"❌ Agent Error: {e}")
                st.exception(e)
                
    # ============================================================
    # 💬 MINI CHAT — Agent सँग सोधपुछ (Tool-Enabled, Powerful)
    # ============================================================
    st.markdown("---")
    st.markdown("#### 💬 Agent सँग सोधपुछ गर्नुहोस्")
    st.caption("अघिल्लो नतिजामा आधारित प्रश्न सोध्नुहोस्, वा थप काम दिनुहोस्। (Tools enabled)")

    # ---- Context (अघिल्लो नतिजा) ----
    agent_context = st.session_state.get("agent_result", "")
    if agent_context:
        with st.expander("📋 अघिल्लो नतिजा (Context)"):
            st.markdown(agent_context[:1500])

    # ---- History init ----
    if "agent_mini_chat" not in st.session_state:
        st.session_state.agent_mini_chat = []

    # ---- पुरानो कुराकानी देखाउने ----
    for msg in st.session_state.agent_mini_chat:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-q-box">👤 <b>तपाईं:</b><br>{msg["content"]}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="chat-a-box">🤖 <b>Agent:</b><br>{msg["content"]}</div>',
                unsafe_allow_html=True
            )

    # ---- Chat Input ----
    mini_q = st.chat_input("Agent लाई प्रश्न सोध्नुहोस्...", key="agent_mini_chat_input")

    if mini_q:
        # User message save
        st.session_state.agent_mini_chat.append({"role": "user", "content": mini_q})
        
        # Auto-extract memories from user message
        if len(mini_q.strip()) > 10:
            extract_memories_from_text(st.session_state.user, mini_q, "")

        with st.spinner("🤖 Agent ले काम गर्दैछ..."):
            try:
                client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                chat = client.chats.create(
                    model="gemini-3.5-flash-lite",
                    config=types.GenerateContentConfig(
                        tools=AGENT_TOOLS_V2,
                        temperature=0.1,
                    )
                )
                
                memory_ctx = get_memory_context(st.session_state.user)
                last_summary = get_latest_summary(st.session_state.user)

                # ✅ Mini Chat को System Hint (Universal Multilingual Support)
                memory_ctx = get_memory_context(st.session_state.user)
                last_summary = get_latest_summary(st.session_state.user)

                system_hint = (
                    f"You are a powerful autonomous agent with tools.\n\n"
                    f"🌍 LANGUAGE RULE:\n"
                    f"You MUST reply in the EXACT SAME LANGUAGE as the user's question. "
                    f"(e.g., if the user asks in French, reply in French; if in Arabic, reply in Arabic; if in Nepali, reply in Nepali). "
                    f"Never translate the user's language to English unless requested.\n\n"
                    f"🧠 LONG-TERM MEMORY:\n{memory_ctx if memory_ctx else '(no memories yet)'}\n\n"
                    f"📝 LAST CONVERSATION SUMMARY:\n{last_summary if last_summary else '(none)'}\n\n"
                    f"📋 Previous result context:\n{agent_context[:2000] if agent_context else '(none)'}\n\n"
                    f"👤 User's request: {mini_q}\n\n"
                    f"⚠️ CRITICAL RULES:\n"
                    f"1. If user asks for current data (price, news, **weather**, temperature, forecast), use **tool_web_search**.\n"
                    f"2. When showing web search results, **QUOTE THE EXACT NUMBERS** from the search result.\n"
                    f"3. If user asks for email, use **tool_send_email**.\n"
                    f"4. Be concise but complete.\n"
                )
                
                response = chat.send_message(system_hint)

                # ---- Multi-step tool loop ----
                max_mini_steps = 8
                step = 0
                final_answer = ""
                mini_logs = []

                while step < max_mini_steps:
                    step += 1

                    if response.function_calls:
                        function_responses = []
                        for tool_call in response.function_calls:
                            tool_name = tool_call.name
                            tool_args = dict(tool_call.args) if tool_call.args else {}
                            call_id = tool_call.id

                            mini_logs.append(f"🔧 Step {step}: `{tool_name}` args={str(tool_args)[:150]}")

                                                        # ✅ Audit: agent tool call
                            log_action(st.session_state.user, "AGENT_TOOL", tool_name, "started", str(tool_args)[:200])
                            
                            # ---- Tool Dispatch ----
                            try:
                                if tool_name == "tool_search_files":
                                    result = tool_search_files(**tool_args)
                                elif tool_name == "tool_read_any_file":
                                    result = tool_read_any_file(**tool_args)
                                elif tool_name == "tool_send_message":
                                    result = tool_send_message(**tool_args)
                                elif tool_name == "tool_write_file":
                                    result = tool_write_file(**tool_args)
                                elif tool_name == "tool_run_python":
                                    result = tool_run_python(**tool_args)
                                elif tool_name == "tool_list_directory":
                                    result = tool_list_directory(**tool_args)
                                elif tool_name == "tool_summarize_pdf":
                                    result = tool_summarize_pdf(**tool_args)
                                elif tool_name == "tool_send_email":
                                    result = tool_send_email(**tool_args)
                                #elif tool_name == "tool_send_whatsapp":
                                    #result = tool_send_whatsapp(**tool_args)
                                elif tool_name == "tool_google_sheets_write":
                                    result = tool_google_sheets_write(**tool_args)
                                elif tool_name == "tool_google_drive_upload":
                                    result = tool_google_drive_upload(**tool_args)
                                elif tool_name == "tool_google_drive_search":
                                    result = tool_google_drive_search(**tool_args)
                                elif tool_name == "tool_analyze_image":
                                    result = tool_analyze_image(**tool_args)
                                else:
                                    result = f"Unknown tool: {tool_name}"
                            except Exception as tool_err:
                                result = f"❌ Tool error ({tool_name}): {tool_err}"

                            mini_logs.append(f"   ↳ Result: {str(result)[:250]}")

                            function_responses.append(
                                types.Part.from_function_response(
                                    name=tool_name,
                                    response={"result": str(result)},
                                    #id=call_id
                                )
                            )

                        response = chat.send_message(function_responses)
                    else:
                        final_answer = response.text or "(no answer)"
                        break

                if not final_answer:
                    final_answer = "⚠️ Max steps reached. " + str(response.text)[:300]

                answer = final_answer

                # Logs देखाउने (expandable)
                if mini_logs:
                    with st.expander(f"📋 Tool Logs ({len(mini_logs)})"):
                        for log in mini_logs:
                            st.text(log)

            except Exception as e:
                answer = f"❌ Error: {e}"

        # Agent answer save
        st.session_state.agent_mini_chat.append({"role": "assistant", "content": answer})
        
                # Save memory from AI answer
        extract_memories_from_text(st.session_state.user, mini_q, answer)

        # Auto-summarize every 10 messages
        if len(st.session_state.agent_mini_chat) % 10 == 0:
            summarize_conversation(st.session_state.user, st.session_state.agent_mini_chat)
            
        st.rerun()

    # ---- Clear Chat ----
    if st.session_state.agent_mini_chat:
        if st.button("🗑️ Chat Clear", key="agent_mini_chat_clear"):
            st.session_state.agent_mini_chat = []
            st.rerun()

# ============================================================
# 🎬 TAB 5: CAPCUT-STYLE VIDEO EDITOR
# ============================================================
with tab_video:
    st.markdown("## 🎬 Powerful Video Editor")
    st.caption("Trim, Text, Music, Filter, Effect — MoviePy powered")

    uploaded_video = st.file_uploader("भिडियो अपलोड गर्नुहोस्", type=["mp4", "mov", "avi", "mkv"], key="editor_upload")

    if uploaded_video:
        os.makedirs("temp_edits", exist_ok=True)
        input_path = os.path.join("temp_edits", uploaded_video.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_video.getbuffer())

        # Video Preview
        st.video(input_path)

        # Tabs for Editor Tools (CapCut जस्तै)
        edit_tab1, edit_tab2, edit_tab3, edit_tab4, edit_tab5 = st.tabs([
            "✂️ Trim", "🎵 Music", "🔤 Text", "🎨 Filter", "⚡ Effect"
        ])

        output_path = os.path.join("temp_edits", f"edited_{uploaded_video.name}")

        # ---- 1. TRIM ----
        with edit_tab1:
            st.markdown("### ✂️ Trim (काट्ने)")
            col1, col2 = st.columns(2)
            with col1:
                start_t = st.number_input("Start Time (sec)", 0.0, 600.0, 0.0, key="t_start")
            with col2:
                end_t = st.number_input("End Time (sec)", 0.0, 600.0, 10.0, key="t_end")

            if st.button("✂️ Trim Video", type="primary", use_container_width=True):
                with st.spinner("काट्दै..."):
                    res = trim_video(input_path, output_path, start_t, end_t)
                if res["success"]:
                    st.success("✅ Trimmed successfully!")
                    st.video(output_path)
                    with open(output_path, "rb") as f:
                        st.download_button("⬇️ Download Trimmed Video", data=f.read(), file_name="trimmed.mp4", mime="video/mp4")
                else:
                    st.error(f"❌ {res['error']}")

        # ---- 2. MUSIC ----
        with edit_tab2:
            st.markdown("### 🎵 Add Music")
            audio_file = st.file_uploader("Music अपलोड गर्नुहोस् (MP3)", type=["mp3", "wav"], key="music_upload")
            volume = st.slider("Volume", 0.0, 1.0, 0.5, key="vol_slider")

            if audio_file:
                audio_path = os.path.join("temp_edits", audio_file.name)
                with open(audio_path, "wb") as f:
                    f.write(audio_file.getbuffer())

                if st.button("🎵 Add Music", type="primary", use_container_width=True):
                    with st.spinner("गीत मिलाउँदै..."):
                        res = add_music(input_path, audio_path, output_path, volume)
                    if res["success"]:
                        st.success("✅ Music added!")
                        st.video(output_path)
                        with open(output_path, "rb") as f:
                            st.download_button("⬇️ Download with Music", data=f.read(), file_name="music_video.mp4", mime="video/mp4")
                    else:
                        st.error(f"❌ {res['error']}")

        # ---- 3. TEXT ----
        with edit_tab3:
            st.markdown("### 🔤 Add Text")
            txt_input = st.text_input("Text लेख्नुहोस्", "Hello World")
            col1, col2, col3 = st.columns(3)
            with col1:
                txt_pos = st.selectbox("Position", ["bottom", "center", "top"])
            with col2:
                txt_size = st.slider("Size", 20, 100, 50)
            with col3:
                txt_color = st.color_picker("Color", "#FFFFFF")

            if st.button("🔤 Add Text", type="primary", use_container_width=True):
                with st.spinner("टेक्स्ट राख्दै..."):
                    res = add_text(input_path, output_path, txt_input, txt_pos, txt_size, txt_color)
                if res["success"]:
                    st.success("✅ Text added!")
                    st.video(output_path)
                    with open(output_path, "rb") as f:
                        st.download_button("⬇️ Download with Text", data=f.read(), file_name="text_video.mp4", mime="video/mp4")
                else:
                    st.error(f"❌ {res['error']}")

        # ---- 4. FILTER ----
        with edit_tab4:
            st.markdown("### 🎨 Filters")
            filter_type = st.selectbox("Filter Type", ["cinematic", "vibrant", "bw", "warm"], key="f_select")

            if st.button("🎨 Apply Filter", type="primary", use_container_width=True):
                with st.spinner("फिल्टर लगाउँदै..."):
                    res = apply_filter(input_path, output_path, filter_type)
                if res["success"]:
                    st.success("✅ Filter applied!")
                    st.video(output_path)
                    with open(output_path, "rb") as f:
                        st.download_button("⬇️ Download Filtered", data=f.read(), file_name="filtered.mp4", mime="video/mp4")
                else:
                    st.error(f"❌ {res['error']}")

        # ---- 5. EFFECT ----
        with edit_tab5:
            st.markdown("### ⚡ Effects")
            effect_type = st.selectbox("Effect Type", ["slowmo", "fastmo"], key="e_select")

            if st.button("⚡ Apply Effect", type="primary", use_container_width=True):
                with st.spinner("इफेक्ट लगाउँदै..."):
                    res = apply_effect(input_path, output_path, effect_type)
                if res["success"]:
                    st.success("✅ Effect applied!")
                    st.video(output_path)
                    with open(output_path, "rb") as f:
                        st.download_button("⬇️ Download Effect", data=f.read(), file_name="effect_video.mp4", mime="video/mp4")
                else:
                    st.error(f"❌ {res['error']}")

    else:
        st.info("👆 माथि भिडियो अपलोड गर्नुहोस्")

# ============================================================
# 💬 TAB 6: UNIVERSAL AI CAPTION & VIDEO TRANSLATOR
# ============================================================
# ⚠️ app.py को माथि यो import थप्न नबिर्सनुहोस्:
# from caption_translator import translate_srt_gemini
# from caption_maker import generate_srt
#from subtitle_tools import burn_subtitles, parse_srt, save_srt

# ============================================================
# 💬 TAB 6: UNIVERSAL AI CAPTION & VIDEO TRANSLATOR
# ============================================================
with tab_caption:

    st.markdown("## 🌍 Universal AI Caption & Translator")
    st.caption("Whisper AI + Gemini AI + Subtitle Editor")

    uploaded_cap_video = st.file_uploader(
        "🎬 भिडियो अपलोड गर्नुहोस्",
        type=["mp4", "mov", "avi", "mkv"],
        key="caption_video_uploader"
    )

    if uploaded_cap_video:
        os.makedirs("temp_captions", exist_ok=True)
        
        safe_name = Path(uploaded_cap_video.name).name
        video_stem = Path(safe_name).stem
        video_path = os.path.join("temp_captions", safe_name)

        with open(video_path, "wb") as f:
            f.write(uploaded_cap_video.getbuffer())

        st.video(video_path)

        st.markdown("---")
        
        # ---- Settings ----
        col1, col2 = st.columns(2)
        with col1:
            model_size = st.selectbox("🧠 Whisper AI Model", ["small", "medium", "large-v3"], index=0)
        with col2:
            source_options = {"🌐 Auto Detect": None, "नेपाली": "ne", "English": "en", "हिन्दी": "hi"}
            source_name = st.selectbox("🎤 Video Original Language", list(source_options.keys()))
        
        selected_lang = source_options[source_name]

        # Target language
        target_languages_list = ["Nepali", "English", "Hindi", "Chinese", "Japanese", "Korean", "French", "Spanish"]
        target_language_name = st.selectbox("भिडियोलाई कुन भाषामा अनुवाद गर्ने?", target_languages_list, index=0)

        # ---- Generate Button ----
        if st.button("🚀 Generate & Translate Captions", type="primary", use_container_width=True, key="generate_caption_btn"):
            
            original_srt = os.path.join("temp_captions", f"{video_stem}_original.srt")
            translated_srt = os.path.join("temp_captions", f"{video_stem}_{target_language_name}.srt")

            with st.spinner(f"🎤 Whisper AI ले आवाज पहिचान गर्दैछ..."):
                result = generate_srt(video_path, original_srt, model_size=model_size, language=selected_lang)

            if result["success"]:
                st.success(f"✅ Voice Recognition Complete! ({result['segments']} segments)")
                
                with st.spinner(f"🌍 Gemini AI ले {target_language_name} मा अनुवाद गर्दैछ..."):
                    translation_result = translate_srt_gemini(original_srt, translated_srt, target_language_name)

                if translation_result["success"]:
                    st.success(f"🎉 Translation Complete! Target: {target_language_name}")
                    # session state मा सेभ गर्ने
                    st.session_state['srt_generated'] = True
                    st.session_state['original_srt'] = original_srt
                    st.session_state['translated_srt'] = translated_srt
                else:
                    st.error(f"❌ Translation Error: {translation_result['error']}")

        # ============================================================
        # Subtitle Editor & Burn-in (यदि SRT तयार भइसक्यो भने)
        # ============================================================
        if st.session_state.get('srt_generated'):
            st.markdown("---")
            st.markdown("### 📝 Subtitle Editor & Burn-in")
            
            # १. Subtitle Editor
            srt_to_edit = st.session_state['translated_srt']
            blocks = parse_srt(srt_to_edit)
            
            with st.expander("✏️ Edit Translated Subtitles", expanded=False):
                edited_blocks = []
                for b in blocks:
                    col_t, col_txt = st.columns([1, 4])
                    with col_t:
                        st.markdown(f"**{b['time']}**")
                    with col_txt:
                        new_text = st.text_area(
                            f"Line {b['index']}", 
                            value=b['text'], 
                            height=68, 
                            key=f"edit_srt_{b['index']}"
                        )
                        edited_blocks.append({
                            "index": b["index"],
                            "time": b["time"],
                            "text": new_text
                        })
                
                if st.button("💾 Save Edited Subtitles"):
                    save_srt(edited_blocks, srt_to_edit)
                    st.success("✅ Subtitle updated!")
                    st.rerun()

            # २. Burn-in Subtitles
            st.markdown("### 🔥 Burn-in Subtitles (भिडियोमै टाँस्ने)")
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                font_size = st.slider("Font Size", 12, 48, 24)
            with col_f2:
                font_color_hex = st.color_picker("Font Color", "#FFFFFF")
            # Hex to ASS BGR format
            hex_c = font_color_hex.lstrip("#")
            font_ass = f"{hex_c[4:6]}{hex_c[2:4]}{hex_c[0:2]}"

            if st.button("🔥 Burn Subtitles into Video", type="primary"):
                burned_video_path = os.path.join("temp_captions", f"{video_stem}_burned.mp4")
                
                with st.spinner("🔥 भिडियोमा क्याप्सन टाँस्दै..."):
                    res = burn_subtitles(
                        video_path, 
                        st.session_state['translated_srt'], 
                        burned_video_path,
                        font_size=font_size,
                        font_color=font_ass
                    )
                
                if res["success"]:
                    st.success("✅ Subtitle burned successfully!")
                    st.video(burned_video_path)
                    
                    with open(burned_video_path, "rb") as f:
                        st.download_button(
                            "⬇️ Download Final Video (Hardcoded Subtitle)",
                            data=f.read(),
                            file_name=f"{video_stem}_final.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
                else:
                    st.error(f"❌ Burn-in error: {res['error']}")

            # ३. Normal Downloads
            st.markdown("### ⬇️ Download SRT")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                with open(st.session_state['original_srt'], "rb") as f:
                    st.download_button("⬇️ Original SRT", data=f.read(), file_name=f"{video_stem}_original.srt", mime="text/plain", use_container_width=True)
            with col_d2:
                with open(st.session_state['translated_srt'], "rb") as f:
                    st.download_button("⬇️ Translated SRT", data=f.read(), file_name=f"{video_stem}_translated.srt", mime="text/plain", use_container_width=True)

    else:
        st.info("👆 माथि भिडियो अपलोड गरेर आफूले चाहेको भाषामा Subtitle बनाउनुहोस्।")

# ============================================================
# 💼 TAB 7: PROJECT & CLIENT MANAGER (CRM)
# ============================================================
with tab_crm:
    st.markdown("## 💼 Client & Project Manager")
    st.caption("तपाईंका ग्राहक (Clients) र उनीहरूको काम (Projects) ट्र्याक गर्नुहोस्।")

    # 3 वटा मुख्य Sub-tabs
    crm_tab1, crm_tab2, crm_tab3 = st.tabs(["📁 Projects", "👥 Clients", "📦 Delivery"])

    # ---- १. Projects Tab ----
    with crm_tab1:
        col_h1, col_h2 = st.columns([3, 1])
        with col_h1:
            st.markdown("### 📋 सबै कामहरू (Projects)")
        with col_h2:
            show_proj_form = st.toggle("➕ नयाँ काम", key="crm_toggle_proj")

        if show_proj_form:
            with st.form("add_project_form"):
                st.markdown("#### नयाँ Project थप्नुहोस्")
                proj_clients = get_clients(st.session_state.user)
                client_options = {c['name']: c['id'] for c in proj_clients}
                
                if not client_options:
                    st.warning("⚠️ पहिले 'Clients' tab मा गएर ग्राहक थप्नुहोस्।")
                else:
                    p_client = st.selectbox("ग्राहक (Client) छान्नुहोस्", list(client_options.keys()))
                    p_title = st.text_input("कामको नाम (Title)")
                    p_desc = st.text_area("विवरण (Description)")
                    p_status = st.selectbox("स्थिति (Status)", ["Pending", "In Progress", "Completed"])
                    p_budget = st.number_input("बजेट (रु.)", min_value=0.0, step=1000.0)
                    p_deadline = st.date_input("डेडलाइन (Deadline)")
                    
                    if st.form_submit_button("💾 सेभ गर्नुहोस्", type="primary"):
                        if p_title and p_client:
                            add_project(
                                st.session_state.user, client_options[p_client], 
                                p_title, p_desc, p_status, p_budget, str(p_deadline)
                            )
                            st.success("✅ Project थपियो!")
                            st.rerun()
                        else:
                            st.error("कामको नाम र ग्राहक अनिवार्य छ।")

        # Project List
        st.markdown("---")
        projects = get_projects(st.session_state.user)
        if not projects:
            st.info("कुनै Project छैन। माथिबाट नयाँ थप्नुहोस्।")
        else:
            for p in projects:
                with st.expander(f"{p['title']} — ({p['client_name']}) — {p['status']}", expanded=False):
                    st.markdown(f"**विवरण:** {p['description']}")
                    st.markdown(f"**बजेट:** रु. {p['budget']:,.2f} | **डेडलाइन:** {p['deadline']}")
                    
                    # Status Change
                    new_status = st.selectbox(
                        "स्थिति परिवर्तन गर्नुहोस्", 
                        ["Pending", "In Progress", "Completed"], 
                        index=["Pending", "In Progress", "Completed"].index(p['status']),
                        key=f"status_{p['id']}"
                    )
                    if new_status != p['status']:
                        if st.button("अपडेट गर्नुहोस्", key=f"upd_{p['id']}"):
                            update_project_status(p['id'], new_status)
                            st.rerun()

    # ---- २. Clients Tab ----
    with crm_tab2:
        col_c1, col_c2 = st.columns([3, 1])
        with col_c1:
            st.markdown("### 👥 ग्राहकहरू (Clients)")
        with col_c2:
            show_client_form = st.toggle("➕ नयाँ ग्राहक", key="crm_toggle_client")

        if show_client_form:
            with st.form("add_client_form"):
                st.markdown("#### नयाँ ग्राहक थप्नुहोस्")
                c_name = st.text_input("नाम (Name)")
                c_email = st.text_input("इमेल (Email)")
                c_phone = st.text_input("फोन (Phone)")
                c_company = st.text_input("कम्पनी (Company)")
                
                if st.form_submit_button("💾 सेव गर्नुहोस्", type="primary"):
                    if c_name:
                        add_client(st.session_state.user, c_name, c_email, c_phone, c_company)
                        st.success("✅ ग्राहक थपियो!")
                        st.rerun()
                    else:
                        st.error("नाम अनिवार्य छ।")

        # Client List
        st.markdown("---")
        clients = get_clients(st.session_state.user)
        if not clients:
            st.info("कुनै ग्राहक छैन। माथिबाट नयाँ थप्नुहोस्।")
        else:
            for c in clients:
                st.markdown(f"👤 **{c['name']}** ({c['company']}) — 📧 {c['email']} | 📞 {c['phone']}")
    # ---- ३. Delivery Tab
    with crm_tab3:
        st.markdown("### 📦 Final File Delivery")
        st.caption("ग्राहकलाई फाइल पठाउन सुरक्षित लिंक बनाउनुहोस्।")
        
        with st.form("delivery_form"):
            d_project = st.text_input("प्रोजेक्टको नाम (Project Name)")
            d_file = st.file_uploader("फाइल अपलोड गर्नुहोस् (PDF, ZIP, Image)", type=["pdf", "zip", "png", "jpg", "docx"])
            
            if st.form_submit_button("🔗 लिंक बनाउनुहोस्", type="primary"):
                if d_file and d_project:
                    os.makedirs("temp_delivery", exist_ok=True)
                    file_path = os.path.join("temp_delivery", d_file.name)
                    with open(file_path, "wb") as f:
                        f.write(d_file.getbuffer())
                    
                    result = create_delivery_link(st.session_state.user, d_project, file_path)
                    if result["success"]:
                        # APP_URL .env बाट लिने (जस्तै: https://myapp.streamlit.app)
                        base_url = os.getenv("APP_URL", "http://localhost:8501")
                        share_link = f"{base_url}/?delivery={result['token']}"
                        
                        st.success("✅ लिंक तयार भयो!")
                        st.code(share_link, language=None)
                        st.info("यो लिंक ग्राहकलाई पठाउनुहोस्।")
                else:
                    st.error("प्रोजेक्टको नाम र फाइल अनिवार्य छ।")
                                                                         
# ============================================================
# 👑 ADMIN TAB (Admin भए मात्र)
# ============================================================
if is_admin and tab_admin is not None:
    with tab_admin:
        render_admin_panel()
                    
# ============================================================
# FOOTER
# ============================================================
stats_final = get_stats()
st.markdown("---")
fcol1, fcol2, fcol3 = st.columns(3)
with fcol1:
    st.markdown("#### 🧠 PDF Brain")
    st.caption(f"**Version:** 52.0 Pro")
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
