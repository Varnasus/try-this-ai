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

# Authentication assumes token.json already created via OAuth
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
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

def load_next_video():
    with open(VIDEO_LOG, 'r', encoding='utf-8') as f:
        entries = [json.loads(line) for line in f if line.strip()]

    for i, entry in enumerate(entries):
        if not entry.get("uploaded", False):
            return entry, i, entries

    return None, None, entries

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
    chosen_thumb = random.choice(entry.get("thumbnails", []))
    entry["thumbnail_used"] = chosen_thumb
    entry["thumbnail_used_at"] = datetime.utcnow().isoformat()

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

    return response['id']

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
