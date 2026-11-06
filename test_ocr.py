# test_ocr.py
import os
import pytesseract
from PIL import Image, ImageDraw
from dotenv import load_dotenv

load_dotenv()
tess_path = os.getenv("TESSERACT_PATH")
if tess_path:
    pytesseract.pytesseract.tesseract_cmd = tess_path

# एउटा test image बनाउने
img = Image.new('RGB', (400, 100), color='white')
d = ImageDraw.Draw(img)
d.text((10, 40), "Hello AI Automation!", fill='black')
img.save("test_image.png")

# OCR test
try:
    result = pytesseract.image_to_string("test_image.png")
    print(f"✅ Tesseract काम गर्छ!")
    print(f"निकालिएको text: {result.strip()}")
except Exception as e:
    print(f"❌ Error: {e}")

# Cleanup
os.remove("test_image.png")