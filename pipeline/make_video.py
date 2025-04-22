import os
from moviepy.video.VideoClip import ImageClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from dotenv import load_dotenv
from PIL import Image

# Load environment variables, if any
load_dotenv()

# File paths
SCRIPT_FILE = "scripts/script_001.md"
AUDIO_FILE = "audio/script_001.mp3"
OUTPUT_VIDEO = "video/script_001.mp4"
BACKGROUND_IMG = "thumbnails/thumb_001_A.png"

def get_script_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip().replace("*", "")

def create_video(script_text):
    print("🎬 Rendering video...")

    # Load audio and calculate duration
    audio = AudioFileClip(AUDIO_FILE)
    duration = audio.duration

    # Background image
    bg = ImageClip(BACKGROUND_IMG).with_duration(duration)
    
    # Calculate new dimensions while maintaining aspect ratio
    current_w, current_h = bg.size
    aspect_ratio = current_w / current_h
    new_h = 1920
    new_w = int(new_h * aspect_ratio)
    
    # Resize using resize method with explicit dimensions
    bg = bg.resized(width=new_w, height=new_h).with_position("center")

    # Text over background
    txt = TextClip(
        text=script_text,
        size=(1080 - 100, None),
        color="white",
        font_size=60,
        font="verdana",
        method='caption'
    ).with_position(("center", "bottom")).with_duration(duration)

    # Combine video and audio
    final = CompositeVideoClip([bg, txt]).with_audio(audio)
    final.write_videofile(OUTPUT_VIDEO, fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    script = get_script_text(SCRIPT_FILE)
    create_video(script)