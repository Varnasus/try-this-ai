import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

# Load secrets from .env
load_dotenv()

# OAuth vars
CLIENT_ID = os.getenv("YT_CLIENT_ID")
CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN")
TOKEN_URI = "https://oauth2.googleapis.com/token"

# Video config
VIDEO_FILE = "video/script_001.mp4"
THUMBNAIL_FILE = "thumbnails/thumb_001_A.png"  # Optional
TITLE = "How to Summon GPT from a PDF"
DESCRIPTION = "In 60 seconds: how to build a PDF Q&A bot using GPT-4o and Python."
TAGS = ["AI", "PDF", "GPT-4", "YouTube Shorts", "Try This AI"]
CATEGORY_ID = "28"  # Tech
PRIVACY_STATUS = "public"  # or "unlisted", "private"

def get_youtube_service():
    creds = Credentials(
        None,
        refresh_token=REFRESH_TOKEN,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_uri=TOKEN_URI,
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    return build("youtube", "v3", credentials=creds)

def upload_video(youtube):
    media = MediaFileUpload(VIDEO_FILE, mimetype="video/mp4", resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": TITLE,
                "description": DESCRIPTION,
                "tags": TAGS,
                "categoryId": CATEGORY_ID
            },
            "status": {
                "privacyStatus": PRIVACY_STATUS
            }
        },
        media_body=media
    )

    print("📤 Uploading video...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"⏳ Upload progress: {int(status.progress() * 100)}%")

    print(f"✅ Upload complete! Video ID: {response['id']}")
    return response["id"]

def set_thumbnail(youtube, video_id):
    if not os.path.exists(THUMBNAIL_FILE):
        print("⚠️ No thumbnail found, skipping...")
        return

    print("📸 Uploading thumbnail...")
    request = youtube.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(THUMBNAIL_FILE)
    )
    request.execute()
    print("✅ Thumbnail set.")

if __name__ == "__main__":
    youtube = get_youtube_service()
    video_id = upload_video(youtube)
    set_thumbnail(youtube, video_id)
