# caption_translator.py — Powerful SRT Translator using Gemini AI
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def translate_srt_gemini(input_srt_path, output_srt_path, target_language_name):
    """
    SRT फाइललाई Gemini AI बाट अनुवाद गर्ने (Context सहित)
    """
    try:
        # १. SRT फाइल पढ्ने
        with open(input_srt_path, "r", encoding="utf-8") as f:
            srt_content = f.read()

        if not srt_content.strip():
            return {"success": False, "error": "SRT फाइल खाली छ"}

        # २. Gemini AI लाई पठाउने
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        prompt = f"""
        You are an expert video subtitle translator. 
        Translate the following SRT subtitle content into **{target_language_name}**.
        
        CRITICAL RULES:
        1. Keep the exact SRT format (Numbers, Timestamps -->, Text).
        2. Translate naturally, keeping the context and emotions.
        3. Do NOT add any extra text or markdown blocks. Just return the SRT text.
        
        SRT Content to translate:
        {srt_content}
        """

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        translated_srt = response.text.strip()

        # Gemini ले कहिलेकाहीँ ```srt ... ``` भनेर markdown हाल्छ, त्यो हटाउने
        if translated_srt.startswith("```"):
            lines = translated_srt.split("\n")
            if lines[0].startswith("```"): lines = lines[1:]
            if lines[-1].startswith("```"): lines = lines[:-1]
            translated_srt = "\n".join(lines)

        # ३. नयाँ फाइलमा सेभ गर्ने
        with open(output_srt_path, "w", encoding="utf-8") as f:
            f.write(translated_srt)

        return {"success": True, "output_path": output_srt_path}

    except Exception as e:
        return {"success": False, "error": str(e)}