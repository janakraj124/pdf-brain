# universal_reader.py — कुनै पनि document पढ्ने
import os
import re
from pypdf import PdfReader
from docx import Document
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from dotenv import load_dotenv

load_dotenv()

tess_path = os.getenv("TESSERACT_PATH")
if tess_path and os.path.exists(tess_path):
    pytesseract.pytesseract.tesseract_cmd = tess_path

POPPLER_PATH = os.getenv("POPPLER_PATH")


# ============================================================
# Document Type Detection
# ============================================================
def detect_document_type(text, filename=""):
    """Document को प्रकार पहिचान"""
    if not text:
        return "unknown"
    
    text_lower = text.lower()[:3000]
    filename_lower = filename.lower()
    
    # Keywords for each type
    patterns = {
        "cv": [
            "curriculum vitae", "resume", "cv", "work experience",
            "employment", "education", "skills", "objective",
            "reference", "personal details", "bio-data"
        ],
        "invoice": [
            "invoice", "bill", "receipt", "amount due",
            "payment", "tax", "vat", "total", "subtotal", "gst"
        ],
        "letter": [
            "dear ", "sincerely", "regards", "yours truly",
            "to whom it may concern", "letter", "correspondence"
        ],
        "contract": [
            "agreement", "contract", "party", "parties",
            "hereby", "whereas", "terms and conditions", "clause"
        ],
        "certificate": [
            "certificate", "certify", "certified", "award",
            "achievement", "completion", "degree", "diploma"
        ],
        "report": [
            "report", "analysis", "findings", "conclusion",
            "recommendation", "executive summary", "methodology"
        ],
        "manual": [
            "manual", "instructions", "how to", "step",
            "warning", "caution", "guide", "troubleshooting"
        ],
        "prescription": [
            "prescription", "rx", "dosage", "medicine",
            "tablet", "capsule", "mg", "twice daily"
        ],
        "medical": [
            "patient", "diagnosis", "symptoms", "treatment",
            "hospital", "doctor", "medical", "clinical"
        ],
        "book": [
            "chapter", "isbn", "publisher", "author",
            "edition", "page", "contents"
        ],
        "article": [
            "abstract", "introduction", "methodology",
            "results", "discussion", "references", "doi"
        ],
        "legal": [
            "court", "judge", "plaintiff", "defendant",
            "case", "law", "section", "act", "petition"
        ],
        "academic": [
            "thesis", "dissertation", "research", "university",
            "department", "faculty", "student", "professor"
        ],
        "business": [
            "business plan", "revenue", "profit", "loss",
            "market", "strategy", "stakeholder", "budget"
        ]
    }
    
    # Filename check first
    for doc_type, kws in patterns.items():
        for kw in kws:
            if kw in filename_lower:
                return doc_type
    
    # Content scoring
    scores = {}
    for doc_type, kws in patterns.items():
        score = sum(1 for kw in kws if kw in text_lower)
        if score > 0:
            scores[doc_type] = score
    
    if scores:
        return max(scores, key=scores.get)
    
    return "general"


# ============================================================
# Multi-Format Reading
# ============================================================
def read_pdf(path):
    """PDF पढ्ने (text वा scanned)"""
    try:
        reader = PdfReader(path)
        
        # Text PDF try
        text = ""
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
        
        # Text छ भने return
        if len(text.strip()) > 100:
            return text
        
        # Scanned PDF → OCR
        return _read_scanned_pdf(path)
    except Exception as e:
        print(f"PDF error: {e}")
        return ""


def _read_scanned_pdf(path):
    """Scanned PDF → OCR"""
    print(f"   📷 Scanned PDF — OCR चल्दै...")
    temp_folder = os.path.join(os.getcwd(), "temp_ocr")
    os.makedirs(temp_folder, exist_ok=True)
    
    try:
        images = convert_from_path(
            path, poppler_path=POPPLER_PATH,
            dpi=200, output_folder=temp_folder
        )
    except Exception as e:
        print(f"   ⚠️ {e}")
        try:
            images = convert_from_path(
                path, poppler_path=POPPLER_PATH,
                dpi=150, use_pdftocairo=True
            )
        except Exception as e2:
            print(f"   ❌ {e2}")
            return ""
    
    text = ""
    total = len(images)
    for i, img in enumerate(images):
        try:
            # English + Nepali
            try:
                page_text = pytesseract.image_to_string(img, lang="eng+nep")
            except Exception:
                page_text = pytesseract.image_to_string(img, lang="eng")
            
            text += page_text + "\n"
        except Exception:
            pass
        
        if (i + 1) % 5 == 0 or (i + 1) == total:
            print(f"   ... {i+1}/{total}")
    
    try:
        import shutil
        shutil.rmtree(temp_folder, ignore_errors=True)
    except Exception:
        pass
    
    return text


def read_docx(path):
    """Word document पढ्ने"""
    try:
        doc = Document(path)
        text = ""
        
        # Paragraphs
        for para in doc.paragraphs:
            text += para.text + "\n"
        
        # Tables
        for table in doc.tables:
            for row in table.rows:
                cells = [cell.text for cell in row.cells]
                text += " | ".join(cells) + "\n"
        
        return text
    except Exception as e:
        print(f"DOCX error: {e}")
        return ""


def read_txt(path):
    """Text file पढ्ने"""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        try:
            with open(path, "r", encoding="latin-1") as f:
                return f.read()
        except Exception:
            return ""


def read_image(path):
    """Image → OCR"""
    try:
        img = Image.open(path)
        
        try:
            text = pytesseract.image_to_string(img, lang="eng+nep")
        except Exception:
            text = pytesseract.image_to_string(img, lang="eng")
        
        return text
    except Exception as e:
        print(f"Image error: {e}")
        return ""


def read_any_document(path):
    """
    कुनै पनि document पढ्ने — auto-detect format
    """
    if not os.path.exists(path):
        return "", "unknown"
    
    ext = path.lower().split(".")[-1]
    
    text = ""
    
    if ext == "pdf":
        text = read_pdf(path)
    elif ext in ["docx", "doc"]:
        text = read_docx(path)
    elif ext in ["txt", "md", "csv", "json", "xml", "html", "htm"]:
        text = read_txt(path)
    elif ext in ["jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff"]:
        text = read_image(path)
    else:
        # Try text
        text = read_txt(path)
    
    # Detect type
    doc_type = detect_document_type(text, os.path.basename(path))
    
    return text, doc_type


def read_all_in_folder(folder):
    """Folder भित्रको सबै documents पढ्ने"""
    if not os.path.exists(folder):
        return {}
    
    supported = [
        ".pdf", ".docx", ".doc", ".txt", ".md",
        ".jpg", ".jpeg", ".png", ".webp", ".bmp"
    ]
    
    files = []
    for f in os.listdir(folder):
        if any(f.lower().endswith(ext) for ext in supported):
            files.append(f)
    
    if not files:
        return {}
    
    all_docs = {}
    for filename in files:
        path = os.path.join(folder, filename)
        print(f"📖 पढ्दै: {filename}")
        try:
            text, doc_type = read_any_document(path)
            if text.strip():
                all_docs[filename] = {
                    "text": text,
                    "type": doc_type
                }
                print(f"   ✅ {len(text)} अक्षर ({doc_type})")
        except Exception as e:
            print(f"   ❌ {e}")
    
    return all_docs


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        path = sys.argv[1]
        print(f"📄 Reading: {path}\n")
        text, doc_type = read_any_document(path)
        print(f"✅ Type: {doc_type}")
        print(f"📊 Length: {len(text)} chars\n")
        print("=" * 60)
        print(text[:1000])
        print("=" * 60)