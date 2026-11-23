
# video_editor.py
# PDF Brain — Professional Video Editor
# Compatible with MoviePy 2.x

import os
import shutil

# --------------------------------------------------
# 1. DIRECT MOVIEPY IMPORTS
# --------------------------------------------------

from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import (
    CompositeVideoClip,
    concatenate_videoclips,
)
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import concatenate_audioclips
from moviepy.video import fx as vfx


# --------------------------------------------------
# 2. HELPER FUNCTIONS
# --------------------------------------------------

def _check_file(path):
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")


def _check_output(output_path):
    if not output_path:
        raise ValueError("Output path is required.")

    folder = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(folder, exist_ok=True)


def _write_video(clip, output_path):
    _check_output(output_path)

    fps = getattr(clip, "fps", None) or 24

    clip.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=fps,
        logger=None,
        threads=2,
    )


def _result_error(error):
    return {
        "success": False,
        "error": str(error),
    }


def _find_font():
    """Find an available Linux font."""

    fonts = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]

    for font in fonts:
        if os.path.isfile(font):
            return font

    raise FileNotFoundError(
        "No supported font found. Install a TTF font."
    )


# --------------------------------------------------
# 3. VIDEO TRIM
# --------------------------------------------------

def trim_video(input_path, output_path, start_time, end_time):

    clip = None
    final = None

    try:
        _check_file(input_path)

        start_time = float(start_time)
        end_time = float(end_time)

        if start_time < 0 or end_time <= start_time:
            raise ValueError("Invalid video trim duration.")

        clip = VideoFileClip(input_path)

        if end_time > clip.duration:
            raise ValueError("End time exceeds video duration.")

        final = clip.subclipped(start_time, end_time)

        _write_video(final, output_path)

        return {
            "success": True,
            "output_path": output_path,
        }

    except Exception as e:
        return _result_error(e)

    finally:
        if final:
            final.close()
        if clip:
            clip.close()


# --------------------------------------------------
# 4. ADD TEXT OVERLAY
# --------------------------------------------------

def add_text(
    input_path,
    output_path,
    text,
    position="bottom",
    fontsize=50,
    color="white",
):

    clip = None
    txt = None
    final = None

    try:
        _check_file(input_path)

        clip = VideoFileClip(input_path)

        font = _find_font()

        fontsize = max(10, min(int(fontsize), 200))

        txt = TextClip(
            font=font,
            text=str(text),
            font_size=fontsize,
            color=color,
            stroke_color="black",
            stroke_width=2,
            method="caption",
            size=(max(100, clip.w - 80), None),
        ).with_duration(clip.duration)

        positions = {
            "top": ("center", 50),
            "center": ("center", "center"),
            "bottom": ("center", clip.h - txt.h - 50),
        }

        pos = positions.get(
            position,
            positions["bottom"],
        )

        txt = txt.with_position(pos)

        final = CompositeVideoClip(
            [clip, txt],
            size=clip.size,
        )

        if clip.audio:
            final = final.with_audio(clip.audio)

        _write_video(final, output_path)

        return {
            "success": True,
            "output_path": output_path,
        }

    except Exception as e:
        return _result_error(e)

    finally:
        if final:
            final.close()
        if txt:
            txt.close()
        if clip:
            clip.close()


# --------------------------------------------------
# 5. ADD BACKGROUND MUSIC
# --------------------------------------------------

def add_music(
    video_path,
    audio_path,
    output_path,
    volume=0.5,
):

    video = None
    audio = None
    audio_loop = None
    final = None

    try:
        _check_file(video_path)
        _check_file(audio_path)

        volume = max(0.0, min(float(volume), 2.0))

        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)

        if not audio.duration or audio.duration <= 0:
            raise ValueError("Invalid audio duration.")

        audio = audio.with_volume_scaled(volume)

        if audio.duration < video.duration:
            loops = int(video.duration / audio.duration) + 1

            audio_loop = concatenate_audioclips(
                [audio] * loops
            ).subclipped(0, video.duration)

        else:
            audio_loop = audio.subclipped(
                0,
                video.duration,
            )

        final = video.with_audio(audio_loop)

        _write_video(final, output_path)

        return {
            "success": True,
            "output_path": output_path,
        }

    except Exception as e:
        return _result_error(e)

    finally:
        if final:
            final.close()
        if audio_loop:
            audio_loop.close()
        if audio:
            audio.close()
        if video:
            video.close()


# --------------------------------------------------
# 6. VIDEO FILTERS
# --------------------------------------------------

def apply_filter(
    input_path,
    output_path,
    filter_type="cinematic",
):

    clip = None
    final = None

    try:
        _check_file(input_path)

        clip = VideoFileClip(input_path)

        filters = {
            "cinematic": [
                vfx.MultiplyColor(0.8)
            ],
            "vibrant": [
                vfx.MultiplyColor(1.3)
            ],
            "bw": [
                vfx.BlackAndWhite()
            ],
            "warm": [
                vfx.MultiplyColor(1.1)
            ],
        }

        if filter_type not in filters:
            raise ValueError(
                f"Unsupported filter: {filter_type}"
            )

        final = clip.with_effects(
            filters[filter_type]
        )

        _write_video(final, output_path)

        return {
            "success": True,
            "output_path": output_path,
        }

    except Exception as e:
        return _result_error(e)

    finally:
        if final:
            final.close()
        if clip:
            clip.close()


# --------------------------------------------------
# 7. VIDEO EFFECTS
# --------------------------------------------------

def apply_effect(
    input_path,
    output_path,
    effect_type="slowmo",
):

    clip = None
    final = None

    try:
        _check_file(input_path)

        clip = VideoFileClip(input_path)

        effects = {
            "slowmo": [
                vfx.MultiplySpeed(0.5)
            ],
            "fastmo": [
                vfx.MultiplySpeed(2.0)
            ],
            "reverse": [
                vfx.TimeMirror()
            ],
        }

        if effect_type not in effects:
            raise ValueError(
                f"Unsupported effect: {effect_type}"
            )

        final = clip.with_effects(
            effects[effect_type]
        )

        _write_video(final, output_path)

        return {
            "success": True,
            "output_path": output_path,
        }

    except Exception as e:
        return _result_error(e)

    finally:
        if final:
            final.close()
        if clip:
            clip.close()


# --------------------------------------------------
# 8. MERGE MULTIPLE VIDEOS
# --------------------------------------------------

def merge_videos(video_paths, output_path):

    clips = []
    final = None

    try:
        if not video_paths or len(video_paths) < 2:
            raise ValueError(
                "At least two videos are required."
            )

        for path in video_paths:
            _check_file(path)
            clips.append(VideoFileClip(path))

        final = concatenate_videoclips(
            clips,
            method="compose",
        )

        _write_video(final, output_path)

        return {
            "success": True,
            "output_path": output_path,
        }

    except Exception as e:
        return _result_error(e)

    finally:
        if final:
            final.close()

        for clip in clips:
            clip.close()
