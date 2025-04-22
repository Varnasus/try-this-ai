import os
import re
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def is_short_form(script_text):
    return len(script_text.split()) < 120

def generate_video_metadata(script_text):
    prompt = f"""
You're writing YouTube metadata for a short, punchy, faceless AI channel called \"Try This AI\". 

The tone should be:
- Bold and attention-grabbing
- Tailored for dev-curious viewers
- Written in plain English
- Avoid clickbait, but keep it edgy
- 100 characters or less for titles

This is for a { "YouTube Short" if is_short_form(script_text) else "full-length video" }.

Based on this script:
\"\"\"
{script_text}
\"\"\"

Return JSON:
{{
  "title": "string (max 100 characters)",
  "description": "1-2 sentence summary with a subtle CTA to try the tool or idea",
  "tags": ["tag1", "tag2", "..."]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{ "role": "user", "content": prompt }],
        temperature=0.7
    )

    raw = response.choices[0].message.content

    try:
        # Extract JSON object from GPT response, ignoring markdown code fencing
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if json_match:
            cleaned = json_match.group(0)
            metadata = json.loads(cleaned)
            return metadata
        else:
            raise ValueError("No JSON object found in GPT response.")

    except Exception as e:
        print(f"❌ Failed to parse GPT response: {e}\n\nRaw content:\n{raw}")
        return {
            "title": script_text.split("\n")[0][:100],
            "description": "",
            "tags": []
        }

if __name__ == "__main__":
    print("🚀 Running test...")

    test_script = """
This is a little-known AI API that can summarize any document instantly. I used it to summarize a 200-page research paper into 3 bullet points.

It's available for free and takes one line of Python to use. Try this AI tool to save hours.
"""

    try:
        metadata = generate_video_metadata(test_script)
        print("✅ Metadata generated:")
        print(json.dumps(metadata, indent=2))
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
