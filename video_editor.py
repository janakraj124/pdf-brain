# video_editor.py — CapCut-Style Powerful Video Editor (MoviePy v2)
import os
from moviepy import (
    VideoFileClip, TextClip, CompositeVideoClip, 
    concatenate_videoclips, AudioFileClip, concatenate_audioclips,
    vfx
)

def trim_video(input_path, output_path, start_time, end_time):
    """भिडियो काट्ने (Trim)"""
    try:
        clip = VideoFileClip(input_path).subclipped(start_time, end_time)
        clip.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
        return {"success": True, "output_path": output_path}
    except Exception as e:
        return {"success": False, "error": str(e)}

def add_text(input_path, output_path, text, position="bottom", fontsize=50, color="white"):
    """Text Overlay थप्ने"""
    try:
        clip = VideoFileClip(input_path)
        
        # Position logic
        pos_map = {
            "top": ("center", 50),
            "center": ("center", "center"),
            "bottom": ("center", clip.h - 150),
        }
        pos = pos_map.get(position, ("center", clip.h - 150))

        # Text clip
        txt = TextClip(
            font="Arial",
            text=text, 
            font_size=fontsize, 
            color=color,
            stroke_color="black", 
            stroke_width=2
        ).with_position(pos).with_duration(clip.duration)

        # Combine
        final = CompositeVideoClip([clip, txt])
        final.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
        return {"success": True, "output_path": output_path}
    except Exception as e:
        return {"success": False, "error": str(e)}

def add_music(video_path, audio_path, output_path, volume=0.5):
    """Music थप्ने"""
    try:
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path).with_volume_scaled(volume)

        # Loop audio if shorter than video
        if audio.duration < video.duration:
            loops = int(video.duration / audio.duration) + 1
            audio = concatenate_audioclips([audio] * loops).subclipped(0, video.duration)
        else:
            audio = audio.subclipped(0, video.duration)

        final = video.with_audio(audio)
        final.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
        return {"success": True, "output_path": output_path}
    except Exception as e:
        return {"success": False, "error": str(e)}

def apply_filter(input_path, output_path, filter_type="cinematic"):
    """Filter थप्ने"""
    try:
        clip = VideoFileClip(input_path)

        if filter_type == "cinematic":
            clip = clip.with_effects([vfx.MultiplyColor(0.8)]) # Darken
        elif filter_type == "vibrant":
            clip = clip.with_effects([vfx.MultiplyColor(1.3)]) # Brighten/Saturate
        elif filter_type == "bw":
            clip = clip.with_effects([vfx.BlackAndWhite()]) # Black & White
        elif filter_type == "warm":
            clip = clip.with_effects([vfx.MultiplyColor(1.1)]) # Slight bright

        clip.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
        return {"success": True, "output_path": output_path}
    except Exception as e:
        return {"success": False, "error": str(e)}

def apply_effect(input_path, output_path, effect_type="slowmo"):
    """Effect थप्ने (Speed change)"""
    try:
        clip = VideoFileClip(input_path)

        if effect_type == "slowmo":
            clip = clip.with_effects([vfx.MultiplySpeed(0.5)]) # Slow 50%
        elif effect_type == "fastmo":
            clip = clip.with_effects([vfx.MultiplySpeed(2.0)]) # Fast 200%
        elif effect_type == "reverse":
            clip = clip.with_effects([vfx.TimeMirror()]) # Reverse

        clip.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
        return {"success": True, "output_path": output_path}
    except Exception as e:
        return {"success": False, "error": str(e)}

def merge_videos(video_paths, output_path):
    """धेरै भिडियो जोड्ने"""
    try:
        clips = [VideoFileClip(p) for p in video_paths]
        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
        return {"success": True, "output_path": output_path}
    except Exception as e:
        return {"success": False, "error": str(e)}