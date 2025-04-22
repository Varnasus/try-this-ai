import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
VIDEO_LOG = "video/metadata.jsonl"
THUMBNAIL_DIR = "thumbnails"
os.makedirs(THUMBNAIL_DIR, exist_ok=True)


def load_entries():
    with open(VIDEO_LOG, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def save_entries(entries):
    with open(VIDEO_LOG, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def generate_image(prompt):
    print(f"🎨 Generating image for: {prompt}")
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1
    )
    image_url = response.data[0].url
    image_data = requests.get(image_url).content
    return Image.open(BytesIO(image_data)).convert("RGBA")


def overlay_text(img, text):
    draw = ImageDraw.Draw(img)
    font_size = 80
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    max_width = img.width - 100
    lines = []
    words = text.split()
    line = ""

    for word in words:
        test_line = f"{line} {word}".strip()
        if draw.textlength(test_line, font=font) <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    lines.append(line)

    y_text = img.height - len(lines)*font_size - 100
    for line in lines:
        width = draw.textlength(line, font=font)
        position = ((img.width - width) // 2, y_text)
        draw.text(position, line, font=font, fill="white")
        y_text += font_size + 10

    return img


def slugify(text):
    return ''.join(c if c.isalnum() else '_' for c in text.lower())[:40]


def generate_thumbnails(entries):
    for entry in entries:
        if entry.get("thumbnail") and os.path.exists(entry["thumbnail"]):
            continue

        prompt = f"{entry['title']} as a dramatic AI-generated scene"
        try:
            img = generate_image(prompt)
            img = overlay_text(img, entry['title'])

            filename = os.path.join(THUMBNAIL_DIR, f"{slugify(entry['title'])}_thumb.png")
            img.save(filename)
            entry["thumbnail"] = filename
            print(f"✅ Saved thumbnail: {filename}")
        except Exception as e:
            print(f"❌ Failed to generate thumbnail for {entry['title']}: {e}")


if __name__ == "__main__":
    entries = load_entries()
    generate_thumbnails(entries)
    save_entries(entries)
    print("✅ All thumbnails updated.")
