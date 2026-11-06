# voice_output.py
from gtts import gTTS

def text_to_speech(text, output_path="answer.mp3", language="ne"):
    """
    Text → Audio
    language: "ne" (नेपाली), "en" (English), "hi" (Hindi)
    """
    try:
        # लामो text लाई सीमित गर्ने
        text_limited = text[:800]
        
        tts = gTTS(text=text_limited, lang=language, slow=False)
        tts.save(output_path)
        return output_path
    except Exception as e:
        print(f"TTS Error: {e}")
        return None