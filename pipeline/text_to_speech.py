import os
from elevenlabs import generate, save, set_api_key
from dotenv import load_dotenv

load_dotenv()

SCRIPT_PATH = "scripts/script_001.md"
OUTPUT_PATH = "audio/script_001.mp3"
VOICE_ID = "Laura"  # or any voice name from your account

def get_script_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip().replace("*", "")

def run_tts(script_text):
    set_api_key(os.getenv("ELEVENLABS_API_KEY"))

    print("🎤 Generating speech...")
    audio = generate(
        text=script_text,
        voice=VOICE_ID,
        model="eleven_monolingual_v1"  # or "eleven_multilingual_v2"
    )

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    save(audio, OUTPUT_PATH)
    print(f"✅ Saved audio to {OUTPUT_PATH}")

if __name__ == "__main__":
    text = get_script_text(SCRIPT_PATH)
    run_tts(text)
