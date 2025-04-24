import os

from dotenv import load_dotenv
from elevenlabs import generate, save, set_api_key

from config import Config, Environment

# Load configuration
Config.load_config(Environment.PRODUCTION)
load_dotenv()


def get_script_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip().replace("*", "")


def run_tts(script_text, output_path=None):
    set_api_key(os.getenv("ELEVENLABS_API_KEY"))

    # Get configuration values
    voice_id = Config.get("api.elevenlabs.default_voice", "Laura")
    model = Config.get("api.elevenlabs.model")
    stability = Config.get("api.elevenlabs.stability")
    similarity_boost = Config.get("api.elevenlabs.similarity_boost")

    print("🎤 Generating speech...")
    audio = generate(
        text=script_text,
        voice=voice_id,
        model=model,
        stability=stability,
        similarity_boost=similarity_boost,
    )

    if output_path:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        save(audio, output_path)
        print(f"✅ Saved audio to {output_path}")
    else:
        return audio


if __name__ == "__main__":
    # Use configured script and audio directories
    script_dir = Config.get("files.directories.scripts")
    audio_dir = Config.get("files.directories.audio")

    text = get_script_text(os.path.join(script_dir, "script_001.md"))
    run_tts(text, os.path.join(audio_dir, "script_001.mp3"))
