# debug_pdf.py
import os
from pypdf import PdfReader
from user_reader import is_text_pdf, read_pdf

# तपाईंको PDF
PDF_PATH = "user_docs/admin/CURRICULUM.pdf"

print("=" * 60)
print(f"🔍 Debug: {PDF_PATH}")
print("=" * 60)

# 1. File check
if not os.path.exists(PDF_PATH):
    print(f"❌ File छैन!")
    print(f"📁 user_docs/admin/ मा के छ:")
    if os.path.exists("user_docs/admin"):
        for f in os.listdir("user_docs/admin"):
            print(f"   • {f}")
    exit()

size_kb = os.path.getsize(PDF_PATH) / 1024
print(f"✅ File भेटियो: {size_kb:.1f} KB\n")

# 2. Text PDF check
is_text = is_text_pdf(PDF_PATH)
print(f"📝 Text PDF: {'✅ हो' if is_text else '❌ छैन (Scanned)'}")

# 3. Pages + text length
reader = PdfReader(PDF_PATH)
print(f"📖 Pages: {len(reader.pages)}\n")

print("📄 Page-by-page text:")
total = 0
for i, page in enumerate(reader.pages[:5], 1):
    text = page.extract_text() or ""
    total += len(text)
    print(f"   Page {i}: {len(text)} chars")

if len(reader.pages) > 5:
    print(f"   ... अरू {len(reader.pages) - 5} pages")

print(f"\n📊 पहिलो 5 pages: {total} chars")

# 4. Sample text
if total > 0:
    print(f"\n📝 पहिलो page को text:")
    print("-" * 60)
    print(reader.pages[0].extract_text()[:500])
    print("-" * 60)
else:
    print(f"\n⚠️  कुनै text निकाल्न सकिएन!")
    print(f"🔍 OCR try गर्दै...")
    
    full_text = read_pdf(PDF_PATH)
    print(f"\n📊 read_pdf() output: {len(full_text)} chars")
    
    if full_text:
        print(f"\n📝 OCR बाट text:")
        print("-" * 60)
        print(full_text[:500])
        print("-" * 60)
    else:
        print("\n❌ OCR पनि असफल!")