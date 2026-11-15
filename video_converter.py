# video_converter.py — PDF Brain Powerful Video Converter
"""
HD Video Converter + Effects + Filters + AI Voice Changer
FFmpeg + Pedalboard powered
"""
import os
import subprocess
import json
from pathlib import Path


# ============================================================
# 🔧 FFMPEG HELPERS
# ============================================================
def get_ffmpeg_path():
    """FFmpeg को path खोज्ने"""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass

    for cmd in ["ffmpeg", "ffmpeg.exe"]:
        try:
            result = subprocess.run([cmd, "-version"], capture_output=True, text=True)
            if result.returncode == 0:
                return cmd
        except FileNotFoundError:
            continue
    return None


def get_ffprobe_path():
    """FFprobe को path"""
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        return None
    if "ffmpeg" in ffmpeg:
        return ffmpeg.replace("ffmpeg", "ffprobe")
    return "ffprobe"


def get_video_info(input_path):
    """भिडियोको जानकारी"""
    ffprobe = get_ffprobe_path()
    if not ffprobe:
        return None

    try:
        result = subprocess.run(
            [ffprobe, "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", input_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        video_stream = next(
            (s for s in data.get("streams", []) if s.get("codec_type") == "video"), None
        )
        if not video_stream:
            return None

        return {
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "codec": video_stream.get("codec_name"),
            "duration": float(data.get("format", {}).get("duration", 0)),
            "size_mb": os.path.getsize(input_path) / (1024 * 1024),
            "fps": video_stream.get("r_frame_rate", "30/1"),
        }
    except Exception as e:
        print(f"[VIDEO INFO ERROR] {e}")
        return None


# ============================================================
# 🎬 HD CONVERTER (Format + Resolution + Quality)
# ============================================================
def convert_to_hd(input_path, output_path, resolution="1080p",
                  target_format="mp4", quality="high",
                  progress_callback=None):
    """
    HD मा convert गर्ने

    Args:
        input_path: Input file
        output_path: Output file
        resolution: "360p", "480p", "720p", "1080p", "1440p", "2160p"
        target_format: "mp4", "mkv", "webm"
        quality: "low", "medium", "high", "ultra"
        progress_callback: function(percent)
    """
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        return {"success": False, "error": "FFmpeg भेटिएन"}

    # Resolution map
    resolutions = {
        "360p": (640, 360),
        "480p": (854, 480),
        "720p": (1280, 720),
        "1080p": (1920, 1080),
        "1440p": (2560, 1440),
        "2160p": (3840, 2160),
    }

    if resolution not in resolutions:
        return {"success": False, "error": f"Resolution '{resolution}' असमर्थित"}

    w, h = resolutions[resolution]

    # Quality map (CRF: कम = राम्रो quality, ठूलो file)
    quality_map = {
        "low": {"crf": 30, "preset": "fast"},
        "medium": {"crf": 23, "preset": "medium"},
        "high": {"crf": 18, "preset": "slow"},
        "ultra": {"crf": 15, "preset": "slower"},
    }
    settings = quality_map.get(quality, quality_map["high"])

    # Format map
    format_map = {
        "mp4": ["-c:v", "libx264", "-c:a", "aac"],
        "webm": ["-c:v", "libvpx-vp9", "-c:a", "libopus"],
        "mkv": ["-c:v", "libx264", "-c:a", "aac"],
    }
    codec_args = format_map.get(target_format, format_map["mp4"])

    # ✅ Powerful HD filter
    vf_filter = (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,"
        f"unsharp=5:5:1.0:5:5:0.5"
    )

    cmd = [
        ffmpeg, "-y",
        "-i", input_path,
        "-vf", vf_filter,
        *codec_args,
        "-crf", str(settings["crf"]),
        "-preset", settings["preset"],
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_path
    ]

    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True
        )

        info = get_video_info(input_path)
        total_sec = info["duration"] if info else 0

        for line in process.stderr:
            if progress_callback and total_sec > 0 and "time=" in line:
                try:
                    time_str = line.split("time=")[1].split(" ")[0]
                    hh, mm, ss = time_str.split(":")
                    current_sec = int(hh) * 3600 + int(mm) * 60 + float(ss)
                    percent = min(100, int((current_sec / total_sec) * 100))
                    progress_callback(percent)
                except:
                    pass

        process.wait()

        if process.returncode == 0:
            return {
                "success": True,
                "output_path": output_path,
                "size_mb": os.path.getsize(output_path) / (1024 * 1024)
            }
        return {"success": False, "error": "FFmpeg failed"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def quick_hd_convert(input_path, output_path, resolution="1080p"):
    """Quick HD convert"""
    return convert_to_hd(input_path, output_path, resolution=resolution, quality="high")


def compress_video(input_path, output_path, quality="medium"):
    """Size कम गर्ने"""
    quality_map = {
        "low": {"crf": 30, "preset": "fast"},
        "medium": {"crf": 23, "preset": "medium"},
        "high": {"crf": 18, "preset": "slow"},
    }
    settings = quality_map.get(quality, quality_map["medium"])
    return convert_to_hd(
        input_path, output_path, resolution="1080p",
        quality=quality
    )


# ============================================================
# 🎨 HD EFFECTS (Glow, Glitch, CRT, Chromatic, Vintage)
# ============================================================
def apply_hd_effect(input_path, output_path, effect="glow", intensity="medium"):
    """
    HD Effect apply गर्ने
    effect: glow, glitch, crt, chromatic, vintage
    intensity: low, medium, high
    """
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        return {"success": False, "error": "FFmpeg भेटिएन"}

    # Effect filters (intensity सहित)
    effect_filters = {
        "glow": "gblur=sigma=20:steps=6,eq=brightness=0.05:saturation=1.2",
        "glitch": "rgbashift=rh=5:bh=-5,noise=alls=20:allf=t+u",
        "crt": "curves=preset=color_negative,eq=contrast=1.3:saturation=1.5,noise=alls=10:allf=t",
        "chromatic": "rgbashift=rh=8:gh=0:bh=-8",
        "vintage": "curves=preset=vintage,eq=saturation=0.7:contrast=1.1,noise=alls=8:allf=t",
    }

    filter_str = effect_filters.get(effect, effect_filters["glow"])

    cmd = [
        ffmpeg, "-y",
        "-i", input_path,
        "-vf", filter_str,
        "-c:v", "libx264",
        "-crf", "20",
        "-preset", "medium",
        "-c:a", "copy",
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            return {"success": True, "output_path": output_path}
        return {"success": False, "error": result.stderr[:300]}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# 🎨 HD FILTERS (Color Grading)
# ============================================================
def apply_hd_filter(input_path, output_path, filter_type="cinematic"):
    """
    HD Filter apply गर्ने
    filter_type: cinematic, vibrant, moody, warm
    """
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        return {"success": False, "error": "FFmpeg भेटिएन"}

    filter_map = {
        "cinematic": (
            "eq=contrast=1.15:saturation=1.1:brightness=-0.02,"
            "colorbalance=rs=0.12:gs=-0.04:bs=-0.15:rm=0.08:gm=-0.02:bm=-0.08,"
            "curves=all='0/0.02 0.5/0.5 1/0.98',"
            "unsharp=5:5:0.6"
        ),
        "vibrant": (
            "eq=saturation=1.25:contrast=1.18:brightness=0.01:gamma=1.05,"
            "colorbalance=rs=0.05:bs=-0.05,"
            "unsharp=5:5:0.7"
        ),
        "moody": (
            "eq=saturation=0.95:contrast=1.25:brightness=-0.03,"
            "curves=all='0/0.05 0.5/0.48 1/0.95',"
            "colorbalance=bs=0.08:bh=-0.05,"
            "unsharp=5:5:0.5"
        ),
        "warm": (
            "eq=saturation=1.1:contrast=1.05:brightness=0.02,"
            "colorbalance=rs=0.1:bs=-0.1,"
            "unsharp=5:5:0.4"
        ),
    }

    vf = filter_map.get(filter_type, filter_map["cinematic"])

    cmd = [
        ffmpeg, "-y",
        "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264",
        "-crf", "20",
        "-preset", "medium",
        "-c:a", "copy",
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            return {"success": True, "output_path": output_path}
        return {"success": False, "error": result.stderr[:300]}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# 🎤 AI VOICE CHANGER (Pedalboard)
# ============================================================
def change_voice_pitch(input_audio_path, output_audio_path, semitones=4):
    """
    AI Voice Changer (Pedalboard)
    semitones: +4 (मोटो/गहिरो), -4 (पातलो/उच्च)
    """
    try:
        from pedalboard import Pedalboard, PitchShift
        from pedalboard.io import AudioFile

        with AudioFile(input_audio_path) as f:
            audio = f.read(f.frames)
            samplerate = f.samplerate

        board = Pedalboard([PitchShift(semitones=semitones)])

        effected = board(audio, samplerate)

        with AudioFile(output_audio_path, "w", samplerate, effected.shape[0]) as f:
            f.write(effected)

        return {"success": True, "output_path": output_audio_path}
    except ImportError:
        return {
            "success": False,
            "error": "Pedalboard install गर्नुहोस्: pip install pedalboard"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# 🎵 AUDIO EXTRACT
# ============================================================
def extract_audio(input_path, output_path, format="mp3"):
    """भिडियोबाट audio निकाल्ने"""
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        return {"success": False, "error": "FFmpeg भेटिएन"}

    if format == "mp3":
        codec_args = ["-acodec", "libmp3lame", "-q:a", "2"]
    elif format == "wav":
        codec_args = ["-acodec", "pcm_s16le"]
    elif format == "aac":
        codec_args = ["-acodec", "aac", "-b:a", "192k"]
    else:
        codec_args = ["-acodec", "libmp3lame", "-q:a", "2"]

    cmd = [ffmpeg, "-y", "-i", input_path, "-vn", *codec_args, output_path]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            return {"success": True, "output_path": output_path}
        return {"success": False, "error": result.stderr[:200]}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# 🔥 COMBINED: HD + Effect + Filter
# ============================================================
def convert_with_effect(input_path, output_path, resolution="1080p",
                        effect=None, filter_type=None, quality="high"):
    """
    एकैचोटि HD + Effect + Filter
    """
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        return {"success": False, "error": "FFmpeg भेटिएन"}

    resolutions = {
        "360p": (640, 360), "480p": (854, 480), "720p": (1280, 720),
        "1080p": (1920, 1080), "1440p": (2560, 1440), "2160p": (3840, 2160),
    }
    w, h = resolutions.get(resolution, (1920, 1080))

    quality_map = {
        "low": {"crf": 30, "preset": "fast"},
        "medium": {"crf": 23, "preset": "medium"},
        "high": {"crf": 18, "preset": "slow"},
        "ultra": {"crf": 15, "preset": "slower"},
    }
    settings = quality_map.get(quality, quality_map["high"])

    # Build filter chain
    filters = [
        f"scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos",
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
        "unsharp=5:5:1.0:5:5:0.5"
    ]

    # Add effect
    effect_filters = {
        "glow": "gblur=sigma=20:steps=6,eq=brightness=0.05:saturation=1.2",
        "glitch": "rgbashift=rh=5:bh=-5,noise=alls=20:allf=t+u",
        "crt": "curves=preset=color_negative,eq=contrast=1.3:saturation=1.5",
        "chromatic": "rgbashift=rh=8:gh=0:bh=-8",
        "vintage": "curves=preset=vintage,eq=saturation=0.7:contrast=1.1",
    }
    if effect and effect in effect_filters:
        filters.append(effect_filters[effect])

    # Add filter
    filter_map = {
        "cinematic": "eq=contrast=1.15:saturation=1.1,colorbalance=rs=0.12:bs=-0.15",
        "vibrant": "eq=saturation=1.25:contrast=1.18,colorbalance=rs=0.05:bs=-0.05",
        "moody": "eq=saturation=0.95:contrast=1.25,colorbalance=bs=0.08",
        "warm": "eq=saturation=1.1:brightness=0.02,colorbalance=rs=0.1:bs=-0.1",
    }
    if filter_type and filter_type in filter_map:
        filters.append(filter_map[filter_type])

    vf = ",".join(filters)

    cmd = [
        ffmpeg, "-y",
        "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264",
        "-crf", str(settings["crf"]),
        "-preset", settings["preset"],
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            return {
                "success": True,
                "output_path": output_path,
                "size_mb": os.path.getsize(output_path) / (1024 * 1024)
            }
        return {"success": False, "error": result.stderr[:300]}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# 🧪 TEST
# ============================================================
if __name__ == "__main__":
    print("🧪 Testing video_converter.py...\n")

    ffmpeg = get_ffmpeg_path()
    if ffmpeg:
        print(f"✅ FFmpeg: {ffmpeg[:60]}...")
    else:
        print("❌ FFmpeg भेटिएन")
        print("   Install: pip install imageio-ffmpeg")

    try:
        import pedalboard
        print(f"✅ Pedalboard: installed")
    except ImportError:
        print("⚠️ Pedalboard: install गर्नुहोस् (pip install pedalboard)")

    print("\n✅ video_converter.py ready!")