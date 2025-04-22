import os
import json
from datetime import datetime
from moviepy.video.VideoClip import ImageClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from dotenv import load_dotenv
from PIL import Image
from text_to_speech import run_tts

# Load environment variables
load_dotenv()

# Paths and configuration
SCRIPT_DIR = "scripts"
AUDIO_DIR = "audio"
VIDEO_DIR = "video"
THUMBNAIL_DIR = "thumbnails"
METADATA_LOG = os.path.join(VIDEO_DIR, "metadata.jsonl")
BACKGROUND_IMG = os.path.join(THUMBNAIL_DIR, "thumb_001_A.png")
VOICE_USED = "Rachel"


def get_script_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip().replace("*", "")


def log_metadata(entry):
    os.makedirs(VIDEO_DIR, exist_ok=True)
    # Prevent duplicate entries based on script and video filename
    if os.path.exists(METADATA_LOG):
        with open(METADATA_LOG, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    existing = json.loads(line)
                    if existing.get("script") == entry["script"] and existing.get("video") == entry["video"]:
                        print(f"⚠️ Metadata already logged for {entry['script']}, skipping log.")
                        return
                except json.JSONDecodeError:
                    continue

    with open(METADATA_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"📝 Metadata logged to {METADATA_LOG}")


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

    # Log metadata (if not already logged)
    log_metadata({
        "script": os.path.basename(script_path),
        "video": video_path,
        "audio": audio_path,
        "thumbnail": BACKGROUND_IMG,
        "title": script_text.split("\n")[0][:100],
        "voice": VOICE_USED,
        "created_at": datetime.now().isoformat(),
        "uploaded": False
    })


if __name__ == "__main__":
    single_script = os.path.join(SCRIPT_DIR, "script_001.md")
    render_video(single_script)
