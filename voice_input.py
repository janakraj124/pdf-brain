# voice_input.py
import speech_recognition as sr

def speech_to_text(audio_file_path=None, language="ne-NP"):
    """
    Audio → Text
    language: "ne-NP" (नेपाली), "en-US" (English), "hi-IN" (Hindi)
    """
    recognizer = sr.Recognizer()
    
    if audio_file_path:
        with sr.AudioFile(audio_file_path) as source:
            audio = recognizer.record(source)
    else:
        with sr.Microphone() as source:
            print("🎤 बोल्नुहोस्...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
    
    try:
        text = recognizer.recognize_google(audio, language=language)
        return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"