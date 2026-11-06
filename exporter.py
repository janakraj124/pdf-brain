# exporter.py
import os
from datetime import datetime


def export_to_text(messages, username, filename=None):
    """Text file मा export"""
    if not filename:
        filename = f"exports/chat_{username}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write(f"  PDF Brain Conversation\n")
        f.write(f"  User: {username}\n")
        f.write(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("=" * 70 + "\n\n")
        
        for msg in messages:
            role = "👤 तपाईं" if msg["role"] == "user" else "🧠 AI"
            f.write(f"{role}:\n")
            f.write(msg["content"] + "\n")
            
            if msg.get("sources"):
                f.write(f"\n📚 स्रोत: {', '.join(msg['sources'])}\n")
            
            f.write("\n" + "-" * 70 + "\n\n")
    
    return filename


def export_to_html(messages, username, filename=None):
    """HTML file मा export"""
    if not filename:
        filename = f"exports/chat_{username}_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    html = """<!DOCTYPE html>
<html lang="ne">
<head>
<meta charset="utf-8">
<title>PDF Brain Conversation</title>
<style>
    body {
        font-family: 'Segoe UI', system-ui, sans-serif;
        max-width: 900px;
        margin: 40px auto;
        padding: 20px;
        background: #f5f7fa;
    }
    h1 {
        background: linear-gradient(90deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2em;
        margin-bottom: 5px;
    }
    .meta {
        color: #666;
        margin-bottom: 30px;
        font-size: 0.9em;
    }
    .message {
        padding: 15px 20px;
        border-radius: 12px;
        margin: 15px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .user {
        background: linear-gradient(135deg, #e7f3ff, #d4e9ff);
        border-left: 4px solid #0066cc;
    }
    .assistant {
        background: white;
        border-left: 4px solid #667eea;
    }
    .role {
        font-weight: 700;
        margin-bottom: 8px;
        color: #333;
    }
    .sources {
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #eee;
        font-size: 0.85em;
        color: #0066cc;
    }
    .source-tag {
        display: inline-block;
        background: #667eea;
        color: white;
        padding: 2px 10px;
        border-radius: 10px;
        font-size: 0.85em;
        margin: 2px;
    }
</style>
</head>
<body>
"""
    html += f"<h1>🧠 PDF Brain Conversation</h1>"
    html += f'<div class="meta">👤 {username} | 📅 {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>'
    
    for msg in messages:
        cls = "user" if msg["role"] == "user" else "assistant"
        role = "👤 तपाईं" if msg["role"] == "user" else "🧠 AI"
        content = msg["content"].replace("\n", "<br>")
        
        html += f'<div class="message {cls}">'
        html += f'<div class="role">{role}</div>'
        html += f'<div>{content}</div>'
        
        if msg.get("sources"):
            html += '<div class="sources">📚 '
            for s in msg["sources"]:
                html += f'<span class="source-tag">{s}</span>'
            html += '</div>'
        
        html += '</div>'
    
    html += "</body></html>"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    
    return filename


def export_to_pdf(messages, username, filename=None):
    """PDF file मा export"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.colors import HexColor
    except ImportError:
        return None
    
    if not filename:
        filename = f"exports/chat_{username}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=50, leftMargin=50,
        topMargin=50, bottomMargin=50
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=HexColor("#667eea"),
        spaceAfter=10
    )
    
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=10,
        textColor=HexColor("#666666"),
        spaceAfter=20
    )
    
    role_user = ParagraphStyle(
        "RoleUser",
        parent=styles["Heading3"],
        fontSize=12,
        textColor=HexColor("#0066cc"),
        spaceBefore=12,
        spaceAfter=6
    )
    
    role_ai = ParagraphStyle(
        "RoleAI",
        parent=styles["Heading3"],
        fontSize=12,
        textColor=HexColor("#667eea"),
        spaceBefore=12,
        spaceAfter=6
    )
    
    content_style = ParagraphStyle(
        "Content",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        spaceAfter=8
    )
    
    source_style = ParagraphStyle(
        "Source",
        parent=styles["Normal"],
        fontSize=9,
        textColor=HexColor("#0066cc"),
        spaceAfter=12
    )
    
    story = []
    
    # Title
    story.append(Paragraph("🧠 PDF Brain Conversation", title_style))
    story.append(Paragraph(
        f"👤 {username} | 📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        meta_style
    ))
    story.append(Spacer(1, 0.2 * inch))
    
    for msg in messages:
        is_user = msg["role"] == "user"
        role_text = "👤 तपाईं" if is_user else "🧠 AI"
        role_style = role_user if is_user else role_ai
        
        story.append(Paragraph(role_text, role_style))
        
        # Content — escape HTML special chars
        content = msg["content"]
        content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        content = content.replace("\n", "<br/>")
        
        story.append(Paragraph(content, content_style))
        
        if msg.get("sources"):
            sources_text = "📚 स्रोत: " + ", ".join(msg["sources"])
            story.append(Paragraph(sources_text, source_style))
        
        story.append(Spacer(1, 0.15 * inch))
    
    doc.build(story)
    return filename


def export_to_docx(messages, username, filename=None):
    """Word (DOCX) file मा export"""
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor, Inches
    except ImportError:
        return None
    
    if not filename:
        filename = f"exports/chat_{username}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx"
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    doc = Document()
    
    # Title
    title = doc.add_heading("🧠 PDF Brain Conversation", level=0)
    
    # Meta
    meta = doc.add_paragraph()
    meta_run = meta.add_run(f"👤 {username} | 📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    meta_run.font.size = Pt(10)
    meta_run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    
    doc.add_paragraph()
    
    for msg in messages:
        is_user = msg["role"] == "user"
        role_text = "👤 तपाईं" if is_user else "🧠 AI"
        
        # Role heading
        heading = doc.add_heading(role_text, level=2)
        if heading.runs:
            run = heading.runs[0]
            if is_user:
                run.font.color.rgb = RGBColor(0x00, 0x66, 0xcc)
            else:
                run.font.color.rgb = RGBColor(0x66, 0x7e, 0xea)
        
        # Content
        doc.add_paragraph(msg["content"])
        
        # Sources
        if msg.get("sources"):
            source_para = doc.add_paragraph()
            source_run = source_para.add_run(f"📚 स्रोत: {', '.join(msg['sources'])}")
            source_run.font.size = Pt(9)
            source_run.font.color.rgb = RGBColor(0x00, 0x66, 0xcc)
            source_run.italic = True
        
        doc.add_paragraph()
    
    doc.save(filename)
    return filename


if __name__ == "__main__":
    # Test
    test_messages = [
        {"role": "user", "content": "यो किताब कसको हो?"},
        {"role": "assistant", "content": "यो किताब DXN Marketing को हो।", "sources": ["sample.pdf"]}
    ]
    
    print("📄 TXT:", export_to_text(test_messages, "test"))
    print("🌐 HTML:", export_to_html(test_messages, "test"))
    print("📕 PDF:", export_to_pdf(test_messages, "test"))
    print("📘 DOCX:", export_to_docx(test_messages, "test"))