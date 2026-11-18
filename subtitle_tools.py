# subtitle_tools.py — Edit and Burn Subtitles
import os
import subprocess
from pathlib import Path

def burn_subtitles(video_path, srt_path, output_path, font_size=24, font_color="white"):
    """
    भिडियोमा सिधै Subtitle टाँस्ने (Burn-in)
    """
    try:
        # FFmpeg को subtitles filter प्रयोग गर्ने
        # (Windows मा path मा \ हुने भएकोले / मा बदल्नुपर्छ)
        safe_srt = str(srt_path).replace("\\", "/").replace(":", "\\:")
        
        # Font style settings
        force_style = f"FontSize={font_size},PrimaryColour=&H{font_color},OutlineColour=&H000000,BorderStyle=1,Outline=2,Shadow=1"

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"subtitles='{safe_srt}':force_style='{force_style}'",
            "-c:a", "copy",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            return {"success": True, "output_path": output_path}
        else:
            return {"success": False, "error": result.stderr[:300]}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def parse_srt(srt_path):
    """SRT फाइल पढेर List मा बदल्ने (Editor को लागि)"""
    blocks = []
    if not os.path.exists(srt_path):
        return blocks
        
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        
    for block in content.split("\n\n"):
        lines = block.split("\n")
        if len(lines) >= 3:
            idx = lines[0]
            time_str = lines[1]
            text = "\n".join(lines[2:])
            blocks.append({
                "index": idx,
                "time": time_str,
                "text": text
            })
    return blocks

def save_srt(blocks, srt_path):
    """Editor बाट List लाई फेरि SRT फाइलमा सेभ गर्ने"""
    with open(srt_path, "w", encoding="utf-8") as f:
        for b in blocks:
            f.write(f"{b['index']}\n{b['time']}\n{b['text']}\n\n")
    return {"success": True}