import os
import json
from datetime import datetime
from googleapiclient.discovery import build
from dotenv import load_dotenv
from generate_thumbnail import generate_thumbnails

load_dotenv()

API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
VIDEO_LOG = 'video/metadata.jsonl'

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]
CREDENTIALS_FILE = "client_secret.json"
TOKEN_PICKLE = "yt_tokens.pkl"


def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PICKLE, 'wb') as token:
            pickle.dump(creds, token)

    return build(API_SERVICE_NAME, API_VERSION, credentials=creds)


def load_entries():
    with open(VIDEO_LOG, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def save_entries(entries):
    with open(VIDEO_LOG, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def update_stats(youtube, entries):
    for entry in entries:
        if not entry.get("uploaded") or not entry.get("youtube_video_id"):
            continue

        try:
            response = youtube.videos().list(
                part="statistics",
                id=entry["youtube_video_id"]
            ).execute()

            stats = response["items"][0]["statistics"]
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))

            last_views = entry.get("views", 0)
            last_check = entry.get("last_checked_at")

            entry["views"] = views
            entry["likes"] = likes
            entry["comments"] = comments
            entry["last_checked_at"] = datetime.utcnow().isoformat()

            print(f"📈 Stats for {entry['title']}: {views} views, {likes} likes")

            # 🚨 Growth Alert Logic
            if last_check:
                try:
                    prev_time = datetime.fromisoformat(last_check)
                    hours_elapsed = (datetime.utcnow() - prev_time).total_seconds() / 3600
                    growth = (views - last_views) / hours_elapsed if hours_elapsed > 0 else 0
                    threshold = 50  # views per hour
                    if growth > threshold:
                        print(f"🚨 Growth alert: {entry['title']} — {views - last_views} new views in {hours_elapsed:.2f}h — {growth:.1f} views/hr")
                except Exception as e:
                    print(f"⚠️ Could not compute growth for {entry['title']}: {e}")

        except Exception as e:
            print(f"❌ Failed to fetch stats for {entry.get('youtube_video_id')}: {e}")


if __name__ == "__main__":
    youtube = get_authenticated_service()
    entries = load_entries()
    update_stats(youtube, entries)
    generate_thumbnails(entries)  # ⬅️ generate multiple thumbnail variants if needed
    save_entries(entries)
    print("✅ All video stats updated.")
