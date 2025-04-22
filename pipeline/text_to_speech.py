import os
from elevenlabs import generate, save, set_api_key
from dotenv import load_dotenv

load_dotenv()

VOICE_ID = "Laura"  # or any voice name from your account

def get_script_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip().replace("*", "")

def run_tts(script_text, output_path=None):
    set_api_key(os.getenv("ELEVENLABS_API_KEY"))

    print("🎤 Generating speech...")
    audio = generate(
        text=script_text,
        voice=VOICE_ID,
        model="eleven_monolingual_v1"  # or "eleven_multilingual_v2"
    )

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        save(audio, output_path)
        print(f"✅ Saved audio to {output_path}")
    else:
        return audio

if __name__ == "__main__":
    text = get_script_text("scripts/script_001.md")
    run_tts(text, "audio/script_001.mp3")
