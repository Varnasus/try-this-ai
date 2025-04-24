import json
import os
from datetime import datetime

from dotenv import load_dotenv
from moviepy.editor import AudioFileClip, CompositeVideoClip, ImageClip, TextClip

from config import Config, Environment
from pipeline.generate_metadata import generate_video_metadata
from pipeline.text_to_speech import run_tts

# Load configuration and environment variables
Config.load_config(Environment.PRODUCTION)
load_dotenv()

# Get configuration values
SCRIPT_DIR = Config.get("files.directories.scripts")
AUDIO_DIR = Config.get("files.directories.audio")
VIDEO_DIR = Config.get("files.directories.video")
THUMBNAIL_DIR = Config.get("files.directories.thumbnails")
METADATA_LOG = os.path.join(VIDEO_DIR, "metadata.jsonl")
DEFAULT_BACKGROUND_IMG = os.path.join(THUMBNAIL_DIR, "thumb_001_A.png")

# Video settings from config
VIDEO_SETTINGS = {
    "width": Config.get("video.resolution.width"),
    "height": Config.get("video.resolution.height"),
    "fps": Config.get("video.fps"),
    "codec": Config.get("video.codec"),
    "bitrate": Config.get("video.bitrate"),
    "audio_bitrate": Config.get("video.audio.bitrate"),
    "audio_sample_rate": Config.get("video.audio.sample_rate"),
    "audio_channels": Config.get("video.audio.channels"),
}


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
                    if (
                        existing.get("script") == entry["script"]
                        and existing.get("video") == entry["video"]
                    ):
                        print(
                            f"⚠️ Metadata already logged for {entry['script']}, skipping log."
                        )
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

    # Use default background if none provided
    if not background_img:
        background_img = DEFAULT_BACKGROUND_IMG

    # Generate audio if it doesn't exist
    if not os.path.exists(audio_path):
        script_text = get_script_text(script_path)
        run_tts(script_text, audio_path)

    # Create video with configured settings
    audio = AudioFileClip(audio_path)
    background = ImageClip(background_img).set_duration(audio.duration)

    # Set video properties from configuration
    background = background.resize(
        width=VIDEO_SETTINGS["width"], height=VIDEO_SETTINGS["height"]
    )

    # Create final video
    final = CompositeVideoClip([background])
    final = final.set_audio(audio)

    # Write video with configured settings
    final.write_videofile(
        video_path,
        fps=VIDEO_SETTINGS["fps"],
        codec=VIDEO_SETTINGS["codec"],
        bitrate=VIDEO_SETTINGS["bitrate"],
        audio_bitrate=VIDEO_SETTINGS["audio_bitrate"],
        audio_fps=VIDEO_SETTINGS["audio_sample_rate"],
        audio_nbytes=2,  # 16-bit audio
        audio_channels=VIDEO_SETTINGS["audio_channels"],
    )

    # Log metadata
    metadata = generate_video_metadata(get_script_text(script_path))
    log_metadata(
        {
            "script": script_path,
            "video": video_path,
            "audio": audio_path,
            "background": background_img,
            "timestamp": datetime.now().isoformat(),
            **metadata,
        }
    )

    return video_path


if __name__ == "__main__":
    single_script = os.path.join(SCRIPT_DIR, "script_001.md")
    render_video(single_script)
