import os
from moviepy.video.VideoClip import ImageClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from dotenv import load_dotenv
from PIL import Image
from text_to_speech import run_tts  # Added for TTS support

# Load environment variables, if any
load_dotenv()

# File paths
SCRIPT_DIR = "scripts"
AUDIO_DIR = "audio"
VIDEO_DIR = "video"
THUMBNAIL_DIR = "thumbnails"
BACKGROUND_IMG = os.path.join(THUMBNAIL_DIR, "thumb_001_A.png")


def get_script_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip().replace("*", "")


def render_video(script_path):
    base_name = os.path.splitext(os.path.basename(script_path))[0]
    audio_path = os.path.join(AUDIO_DIR, f"{base_name}.mp3")
    video_path = os.path.join(VIDEO_DIR, f"{base_name}.mp4")

    script_text = get_script_text(script_path)

    if not os.path.exists(audio_path):
        run_tts(script_text, output_path=audio_path)
    else:
        print(f"🔁 Reusing existing audio: {audio_path}")

    audio = AudioFileClip(audio_path)
    duration = audio.duration

    bg = ImageClip(BACKGROUND_IMG).with_duration(duration)

    current_w, current_h = bg.size
    aspect_ratio = current_w / current_h
    new_h = 1920
    new_w = int(new_h * aspect_ratio)

    bg = bg.resized(width=new_w, height=new_h).with_position("center")

    txt = TextClip(
        text=script_text,
        size=(1080 - 100, None),
        color="white",
        font_size=60,
        font="verdana",
        method='caption'
    ).with_position(("center", "bottom")).with_duration(duration)

    final = CompositeVideoClip([bg, txt]).with_audio(audio)
    final.write_videofile(video_path, fps=24, codec="libx264", audio_codec="aac")


if __name__ == "__main__":
    single_script = os.path.join(SCRIPT_DIR, "script_001.md")
    render_video(single_script)