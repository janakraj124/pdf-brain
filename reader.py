# reader.py
import os
import shutil
import pytesseract
from dotenv import load_dotenv
from pypdf import PdfReader
from pdf2image import convert_from_path

load_dotenv()

# Tesseract setup
tess_path = os.getenv("TESSERACT_PATH")
if tess_path and os.path.exists(tess_path):
    pytesseract.pytesseract.tesseract_cmd = tess_path

POPPLER_PATH = os.getenv("POPPLER_PATH")


def is_text_pdf(path):
    """PDF मा text छ कि scanned हो?"""
    try:
        reader = PdfReader(path)
        for page in reader.pages[:3]:
            text = page.extract_text() or ""
            if len(text.strip()) > 50:
                return True
        return False
    except Exception:
        return False


def read_text_pdf(path):
    """Text-based PDF पढ्ने"""
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += (page.extract_text() or "") + "\n"
    return text


def read_scanned_pdf(path):
    """Scanned PDF — OCR प्रयोग गर्ने"""
    print(f"   🔍 OCR चल्दै (अलि समय लाग्छ)...")
    
    # Temp folder
    temp_folder = r"C:\temp_ocr"
    os.makedirs(temp_folder, exist_ok=True)
    
    images = None
    
    # तरिका १
    try:
        images = convert_from_path(
            path,
            poppler_path=POPPLER_PATH,
            dpi=150,
            output_folder=temp_folder,
            fmt="jpeg",
            paths_only=False
        )
        print(f"   ✅ तरिका १ सफल")
    except Exception as e1:
        print(f"   ⚠️ तरिका १ असफल: {e1}")
        try:
            images = convert_from_path(
                path,
                poppler_path=POPPLER_PATH,
                dpi=150,
                use_pdftocairo=True
            )
            print(f"   ✅ तरिका २ सफल")
        except Exception as e2:
            print(f"   ❌ असफल: {e2}")
            return ""
    
    if not images:
        return ""
    
    # OCR चलाउने
    text = ""
    total = len(images)
    print(f"   📄 {total} pages को OCR सुरु...")
    
    for i, img in enumerate(images):
        page_text = ""
        
        # ⚠️ FIX: Image लाई file मा save गर्ने
        try:
            img_path = os.path.join(temp_folder, f"page_{i+1}.jpg")
            img.save(img_path, "JPEG")
            
            # File बाट OCR
            try:
                page_text = pytesseract.image_to_string(img_path, lang="eng+nep")
            except Exception:
                try:
                    page_text = pytesseract.image_to_string(img_path, lang="eng")
                except Exception as e:
                    print(f"   ⚠️ Page {i+1} OCR error: {e}")
            
            # Cleanup
            try:
                os.remove(img_path)
            except:
                pass
                
        except Exception as e:
            print(f"   ⚠️ Page {i+1} save error: {e}")
        
        text += page_text + "\n"
        
        if (i + 1) % 5 == 0 or (i + 1) == total:
            print(f"   ... {i+1}/{total} pages")
    
    # सबै temp cleanup
    try:
        shutil.rmtree(temp_folder, ignore_errors=True)
    except:
        pass
    
    return text


def read_pdf(path):
    """Smart — text वा scanned auto-detect"""
    if is_text_pdf(path):
        print(f"   📄 Text PDF")
        return read_text_pdf(path)
    else:
        print(f"   📷 Scanned PDF")
        return read_scanned_pdf(path)


def read_all_docs(folder="docs"):
    """docs folder को सबै PDF पढ्ने"""
    if not os.path.exists(folder):
        print(f"❌ '{folder}' folder भेटिएन!")
        return {}
    
    pdfs = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]
    
    if not pdfs:
        print(f"❌ '{folder}' मा कुनै PDF छैन!")
        return {}
    
    print(f"📚 {len(pdfs)} PDF भेटियो\n")
    
    all_texts = {}
    for filename in pdfs:
        path = os.path.join(folder, filename)
        print(f"📖 पढ्दै: {filename}")
        try:
            text = read_pdf(path)
            if text.strip():
                all_texts[filename] = text
                print(f"   ✅ {len(text)} अक्षर\n")
            else:
                print(f"   ⚠️ कुनै text भेटिएन\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
    
    return all_texts


if __name__ == "__main__":
    texts = read_all_docs()
    print(f"\n🎉 जम्मा {len(texts)} files पढियो")
    for name, text in texts.items():
        print(f"   • {name}: {len(text)} अक्षर")