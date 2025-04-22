import os
import json
import random
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

load_dotenv()

# YouTube API setup
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
VIDEO_LOG = 'video/metadata.jsonl'
TOP_PERFORMERS_FILE = 'video/top_performers.json'

# Authentication assumes token.json already created via OAuth
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CREDENTIALS_FILE = "client_secret.json"
TOKEN_PICKLE = "yt_tokens.pkl"

MAX_REUSE = 2
LOCK_SCORE_THRESHOLD = 4.5


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


def load_next_video():
    with open(VIDEO_LOG, 'r', encoding='utf-8') as f:
        entries = [json.loads(line) for line in f if line.strip()]

    for i, entry in enumerate(entries):
        if not entry.get("uploaded", False):
            return entry, i, entries

    return None, None, entries


def choose_thumbnail(entry):
    thumbs = entry.get("thumbnails", [])
    stats = entry.get("thumbnail_stats", {})

    locked = [t for t in thumbs if stats.get(t, {}).get("locked") is True]
    reusable = [
        t for t in thumbs
        if stats.get(t, {}).get("reuse") is True and not stats.get(t, {}).get("disabled") and stats.get(t, {}).get("uses", 0) < MAX_REUSE
    ]
    eligible = [
        t for t in thumbs
        if not stats.get(t, {}).get("disabled")
    ]

    if locked:
        return random.choice(locked)
    elif reusable:
        return random.choice(reusable)
    elif eligible:
        return random.choice(eligible)
    else:
        return random.choice(thumbs)  # fallback


def upload_video(youtube, entry):
    print(f"📤 Uploading: {entry['video']}")
    body = {
        'snippet': {
            'title': entry['title'],
            'description': entry.get('description', ''),
            'tags': entry.get('tags', []),
            'categoryId': '28',  # Science & Technology
        },
        'status': {
            'privacyStatus': 'public'
        }
    }

    media = MediaFileUpload(entry['video'], chunksize=-1, resumable=True)
    request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
    chosen_thumb = choose_thumbnail(entry)
    entry["thumbnail_used"] = chosen_thumb
    entry["thumbnail_used_at"] = datetime.utcnow().isoformat()
    entry.setdefault("thumbnail_stats", {}).setdefault(chosen_thumb, {"uses": 0, "views": 0, "score": 0.0})
    entry["thumbnail_stats"][chosen_thumb]["uses"] += 1

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"🔄 Upload progress: {int(status.progress() * 100)}%")

    print(f"✅ Upload complete! Video ID: {response['id']}")

    # Set the chosen thumbnail after upload
    try:
        thumb_request = youtube.thumbnails().set(
            videoId=response['id'],
            media_body=MediaFileUpload(chosen_thumb)
        )
        thumb_request.execute()
        print(f"🖼️ Thumbnail set: {chosen_thumb}")
    except HttpError as e:
        print(f"⚠️ Failed to set thumbnail: {e}")

    # Initialize performance score
    entry["thumbnail_stats"][chosen_thumb]["last_used_video_id"] = response['id']
    entry["thumbnail_stats"][chosen_thumb]["last_used_at"] = datetime.utcnow().isoformat()

    # Recalculate score: views / uses
    views = entry["thumbnail_stats"][chosen_thumb]["views"]
    uses = entry["thumbnail_stats"][chosen_thumb]["uses"]
    score = round(views / uses, 2) if uses > 0 else 0.0
    entry["thumbnail_stats"][chosen_thumb]["score"] = score

    # Auto-lock top performers
    if score >= LOCK_SCORE_THRESHOLD:
        entry["thumbnail_stats"][chosen_thumb]["locked"] = True
        entry["thumbnail_stats"][chosen_thumb]["locked_at"] = datetime.utcnow().isoformat()

        # Save to global top performers list
        top_record = {
            "thumbnail": chosen_thumb,
            "score": score,
            "views": views,
            "uses": uses,
            "title": entry.get("title"),
            "video_id": response['id'],
            "timestamp": datetime.utcnow().isoformat()
        }
        append_to_top_performers(top_record)

    return response['id']


def append_to_top_performers(record):
    if not os.path.exists(TOP_PERFORMERS_FILE):
        with open(TOP_PERFORMERS_FILE, 'w') as f:
            json.dump([record], f, indent=2)
    else:
        with open(TOP_PERFORMERS_FILE, 'r+') as f:
            data = json.load(f)
            data.append(record)
            f.seek(0)
            json.dump(data, f, indent=2)


def mark_uploaded(index, entries, video_id):
    entries[index]['uploaded'] = True
    entries[index]['youtube_video_id'] = video_id
    with open(VIDEO_LOG, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


if __name__ == '__main__':
    youtube = get_authenticated_service()
    entry, index, entries = load_next_video()

    if not entry:
        print("🎉 All videos have been uploaded!")
        exit(0)

    try:
        video_id = upload_video(youtube, entry)
        mark_uploaded(index, entries, video_id)
    except HttpError as e:
        print(f"❌ Upload failed: {e}")
