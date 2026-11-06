# image_analyzer.py — Powerful Universal Edition
import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.5-flash"


def detect_mime_type(image_path):
    """Image को MIME type"""
    ext = image_path.lower().split(".")[-1]
    mime_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "bmp": "image/bmp",
        "tiff": "image/tiff"
    }
    return mime_map.get(ext, "image/jpeg")


def analyze_image(image_path, question=None, mode="auto"):
    """Powerful Image Analysis"""
    if not os.path.exists(image_path):
        return "❌ Image भेटिएन"
    
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    mime_type = detect_mime_type(image_path)
    
    if mode == "auto" and not question:
        prompt = """तपाईं एक बुद्धिमान AI सहायक हुनुहुन्छ।
यो image लाई **पूरा विश्लेषण** गर्नुहोस्:

१. **के छ?** (Image को प्रकार: photo, document, chart, screenshot)
२. **सबै text** (हुबहु निकाल्नुहोस् — नेपाली + English)
३. **Visual description** (के-के देखिन्छ)
४. **Tables/Charts** (छ भने data पनि)
५. **मुख्य बुँदाहरू** (Important info)

राम्रो format मा, bullet points प्रयोग गरेर दिनुहोस्।"""
    
    elif mode == "text":
        prompt = """यो image मा भएको **सबै text** हुबहु निकाल्नुहोस्।
Layout, formatting जस्तो छ त्यस्तै राख्नुहोस्।
नेपाली + English दुवै support गर्नुहोस्।"""
    
    elif mode == "describe":
        prompt = """यो image लाई **विस्तृत रूपमा describe** गर्नुहोस्:
- के देखिन्छ?
- कुन context हो?
- कुनै text छ?
- Objects, colors, layout?"""
    
    elif mode == "extract_table":
        prompt = """यो image मा **table** छ भने:
१. सबै columns हरू identify गर्नुहोस्
२. सबै rows हरू extract गर्नुहोस्
३. **Markdown table** format मा दिनुहोस्

Table छैन भने "कुनै table भेटिएन" भन्नुहोस्।"""
    
    elif mode == "translate":
        prompt = """यो image मा भएको text:
१. **Original** मा निकाल्नुहोस्
२. **नेपालीमा translate** गर्नुहोस्
३. दुवै पठाउनुहोस्"""
    
    elif question:
        prompt = f"""तपाईं एक सहयोगी AI हुनुहुन्छ।
यो image हेरेर तलको प्रश्नको जवाफ दिनुहोस्:

❓ प्रश्न: {question}

⚠️ नियमहरू:
- Image मा भएको कुरा मात्र भन्नुहोस्
- Text, numbers, names ध्यानपूर्वक हेर्नुहोस्
- राम्रो format मा जवाफ दिनुहोस्
- Image मा छैन भने "image मा भेटिएन" भन्नुहोस्"""
    
    else:
        prompt = """यो image को पूरा विवरण दिनुहोस्।"""
    
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=image_data, mime_type=mime_type),
                prompt
            ]
        )
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)[:200]}"


def extract_text_from_image(image_path):
    """Image बाट text मात्र"""
    return analyze_image(image_path, mode="text")


def extract_table_from_image(image_path):
    """Image बाट table निकाल्ने"""
    return analyze_image(image_path, mode="extract_table")


def ask_about_image(image_path, question):
    """Image बारे specific प्रश्न"""
    return analyze_image(image_path, question=question)


def describe_image(image_path):
    """Image describe"""
    return analyze_image(image_path, mode="describe")


def translate_image_text(image_path):
    """Image को text translate"""
    return analyze_image(image_path, mode="translate")


def extract_numbers_from_image(image_path):
    """Image बाट numbers/amount निकाल्ने"""
    if not os.path.exists(image_path):
        return "❌ Image भेटिएन"
    
    prompt = """यो image मा भएका **सबै numbers, amounts, prices** निकाल्नुहोस्।

Format:
• Item 1: Rs 1,500
• Item 2: $250.50
• Total: Rs 10,000

यदि table छ भने structured format मा दिनुहोस्।"""
    
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    mime_type = detect_mime_type(image_path)
    
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=image_data, mime_type=mime_type),
                prompt
            ]
        )
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)[:200]}"


def extract_names_from_image(image_path):
    """Image बाट names निकाल्ने"""
    if not os.path.exists(image_path):
        return "❌ Image भेटिएन"
    
    prompt = """यो image मा भएका **सबै नामहरू** (नाम, कम्पनी, ठाउँ) निकाल्नुहोस्।

Format:
• व्यक्तिको नाम: ...
• कम्पनी: ...
• ठाउँ: ..."""
    
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    mime_type = detect_mime_type(image_path)
    
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=image_data, mime_type=mime_type),
                prompt
            ]
        )
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)[:200]}"


def extract_dates_from_image(image_path):
    """Image बाट dates निकाल्ने"""
    if not os.path.exists(image_path):
        return "❌ Image भेटिएन"
    
    prompt = """यो image मा भएका **सबै dates र times** निकाल्नुहोस्।

Format:
• Date 1: 2026-10-15
• Time: 13:42
• Duration: ..."""
    
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    mime_type = detect_mime_type(image_path)
    
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=image_data, mime_type=mime_type),
                prompt
            ]
        )
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)[:200]}"


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python image_analyzer.py image.jpg")
        print("  python image_analyzer.py image.jpg text")
        print("  python image_analyzer.py image.jpg table")
        print("  python image_analyzer.py image.jpg numbers")
        print("  python image_analyzer.py image.jpg names")
        print("  python image_analyzer.py image.jpg dates")
        print("  python image_analyzer.py image.jpg describe")
        print("  python image_analyzer.py image.jpg 'प्रश्न'")
        sys.exit()
    
    img_path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "auto"
    
    print("=" * 60)
    print(f"🖼️  Analyzing: {img_path}")
    print(f"🎯 Mode: {mode}")
    print("=" * 60 + "\n")
    
    if mode == "text":
        print(extract_text_from_image(img_path))
    elif mode == "table":
        print(extract_table_from_image(img_path))
    elif mode == "describe":
        print(describe_image(img_path))
    elif mode == "numbers":
        print(extract_numbers_from_image(img_path))
    elif mode == "names":
        print(extract_names_from_image(img_path))
    elif mode == "dates":
        print(extract_dates_from_image(img_path))
    elif mode == "auto":
        print(analyze_image(img_path))
    else:
        print(ask_about_image(img_path, mode))