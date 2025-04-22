import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_video_metadata(script_text):
    prompt = f"""
You are helping write metadata for a faceless YouTube channel about AI.

Script:
\"\"\"
{script_text}
\"\"\"

Respond in this JSON format:
{{
  "title": "...",
  "description": "...",
  "tags": ["...", "...", "..."]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{ "role": "user", "content": prompt }],
        temperature=0.7
    )

    raw = response.choices[0].message.content

    try:
        # Safe eval of returned JSON-like string
        import json
        metadata = json.loads(raw)
        return metadata
    except Exception as e:
        print(f"❌ Failed to parse GPT response: {e}")
        return {
            "title": script_text.split("\\n")[0][:100],
            "description": "",
            "tags": []
        }
