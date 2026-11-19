# caption_maker.py — Auto Caption Generator (Whisper)
import os
import subprocess
from faster_whisper import WhisperModel

# Global model cache
_whisper_model = None

def load_whisper_model(model_size="base"):
    """Whisper model load गर्ने (नेपाली फाइन-ट्युन सहित)"""
    global _whisper_model
    if _whisper_model is None:
        # ✅ नेपालीको लागि विशेष रूपमा तालिम दिइएको मोडेल
        # यदि तपाईंको इन्टरनेट छैन भने, यसले अटोमेटिक रूपमा डाउनलोड गर्नेछ
        _whisper_model = WhisperModel(
            "Dragneel/whisper-medium-nepali-openslr-ct2", 
            device="cpu", 
            compute_type="int8"
        )
    return _whisper_model


def extract_audio_for_whisper(video_path, audio_path):
    """भिडियोबाट 16kHz mono WAV निकाल्ने (Whisper को लागि)"""
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        audio_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def generate_srt(video_path, srt_path, model_size="base", language=None):
    """
    भिडियोबाट SRT सबटाइटल बनाउने

    Args:
        video_path: Input video
        srt_path: Output SRT file
        model_size: "tiny", "base", "small", "medium", "large-v3"
        language: "ne", "en", "hi" वा None (auto-detect)
    """
    # 1. Audio extract
    temp_audio = srt_path.replace(".srt", "_temp.wav")
    if not extract_audio_for_whisper(video_path, temp_audio):
        return {"success": False, "error": "Audio extract failed (FFmpeg)"}

    # 2. Whisper model load
    model = load_whisper_model(model_size)

    # 3. ✅ Powerful Transcribe Settings
    transcribe_params = {
        "beam_size": 5,
        "vad_filter": False,           
        "word_timestamps": False,
        "condition_on_previous_text": False,
    }
    
    if language:
        # ✅ यदि प्रयोगकर्ताले भाषा छानेको छ भने (नेपाली/English/हिन्दी)
        # temperature=0.0 ले गर्दा मोडेलले अन्य भाषामा जाने सम्भावना कम हुन्छ
        transcribe_params["language"] = language
        transcribe_params["temperature"] = 0.0
    else:
        # Auto Detect को लागि temperature list (fallback)
        transcribe_params["temperature"] = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    # ✅ VAD Parameters (गीत/संगीत भएको भिडियोको लागि)
    transcribe_params["vad_filter"] = True
    transcribe_params["vad_parameters"] = {
        "min_silence_duration_ms": 500, 
        "threshold": 0.35  # कम आवाजलाई पनि पहिचान गर्न
    }
    
    try:
        # Transcribe गर्ने
        segments, info = model.transcribe(temp_audio, **transcribe_params)

        # 4. SRT file बनाउने
        srt_content = []
        for i, seg in enumerate(segments, 1):
            start = format_timestamp(seg.start)
            end = format_timestamp(seg.end)
            text = seg.text.strip()
            if text:
                srt_content.append(f"{i}\n{start} --> {end}\n{text}\n")

        # SRT फाइलमा लेख्ने
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_content))

        # Cleanup (temp audio हटाउने)
        if os.path.exists(temp_audio):
            os.remove(temp_audio)

        return {
            "success": True,
            "srt_path": srt_path,
            "language": info.language,
            "language_probability": info.language_probability,
            "segments": len(srt_content)
        }

    except Exception as e:
        # Cleanup on error
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        return {"success": False, "error": f"Transcription failed: {e}"}


def format_timestamp(seconds):
    """SRT timestamp format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"