import os
import json
from datetime import datetime
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, AudioFileClip
from dotenv import load_dotenv
from pipeline.text_to_speech import run_tts
from pipeline.generate_metadata import generate_video_metadata

# Load environment variables
load_dotenv()

# Paths and configuration
SCRIPT_DIR = "scripts"
AUDIO_DIR = "audio"
VIDEO_DIR = "video"
THUMBNAIL_DIR = "thumbnails"
METADATA_LOG = os.path.join(VIDEO_DIR, "metadata.jsonl")
DEFAULT_BACKGROUND_IMG = os.path.join(THUMBNAIL_DIR, "thumb_001_A.png")
VOICE_USED = "Laura"


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


def render_video(script_path, background_img=None):
    base_name = os.path.splitext(os.path.basename(script_path))[0]
    audio_path = os.path.join(AUDIO_DIR, f"{base_name}.mp3")
    video_path = os.path.join(VIDEO_DIR, f"{base_name}.mp4")

    # Create output directories if they don't exist
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    os.makedirs(os.path.dirname(video_path), exist_ok=True)

    script_text = get_script_text(script_path)

    if not os.path.exists(audio_path):
        run_tts(script_text, output_path=audio_path)
    else:
        print(f"🔁 Reusing existing audio: {audio_path}")

    audio = AudioFileClip(audio_path)
    duration = audio.duration

    # Use provided background image or fall back to default
    bg_path = background_img if background_img else DEFAULT_BACKGROUND_IMG
    if not os.path.exists(bg_path):
        raise FileNotFoundError(f"Background image not found: {bg_path}")

    # Create background clip
    bg = ImageClip(bg_path)
    bg = bg.set_duration(duration)
    
    # Resize background
    current_w, current_h = bg.size
    aspect_ratio = current_w / current_h
    new_h = 1920
    new_w = int(new_h * aspect_ratio)
    bg = bg.resize(width=new_w, height=new_h)
    bg = bg.set_position("center")

    # Create text clip with updated parameters
    txt = TextClip(
        script_text,
        size=(980, None),  # Adjusted size to account for padding
        color='white',
        fontsize=60,  # Changed from font_size to fontsize
        font='Verdana',
        method='caption',
        align='center'  # Added alignment
    )
    txt = txt.set_position(("center", "bottom"))
    txt = txt.set_duration(duration)
    txt = txt.margin(bottom=50)  # Add margin at the bottom

    # Compose final video
    final = CompositeVideoClip([bg, txt])
    final = final.set_audio(audio)

    # Write video file with progress bar
    final.write_videofile(
        video_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset='ultrafast',  # Use faster preset for testing
        logger=None  # Disable verbose logging
    )

    # Log metadata
    log_metadata({
        "script": os.path.basename(script_path),
        "video": video_path,
        "audio": audio_path,
        "thumbnail": bg_path,
        "title": script_text.split("\n")[0][:100],
        "voice": VOICE_USED,
        "created_at": datetime.now().isoformat(),
        "uploaded": False,
        **generate_video_metadata(script_text)
    })


if __name__ == "__main__":
    single_script = os.path.join(SCRIPT_DIR, "script_001.md")
    render_video(single_script)
