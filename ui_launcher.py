import json
import os
import pickle
import subprocess
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.VideoClip import ImageClip, TextClip

from pipeline.generate_thumbnail import generate_thumbnails
from pipeline.make_video import render_video
from pipeline.text_to_speech import run_tts
from pipeline.track_video_stats import update_stats
from pipeline.upload_video import upload_video

load_dotenv()

# Config
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
VIDEO_LOG = "video/metadata.jsonl"
CREDENTIALS_FILE = "client_secret.json"
TOKEN_PICKLE = "yt_tokens.pkl"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]
GROWTH_ALERT_THRESHOLD = 50  # views/hour
PIPELINE_DIR = "pipeline"

# Scripts for batch operations
BATCH_RENDER_SCRIPTS = [
    "text_to_speech.py",
    "make_video.py",
    "generate_metadata.py",
    "generate_thumbnail.py",
]
BATCH_UPLOAD_SCRIPT = "upload_next_video.py"


def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PICKLE, "wb") as token:
            pickle.dump(creds, token)
    return build(API_SERVICE_NAME, API_VERSION, credentials=creds)


def load_entries():
    with open(VIDEO_LOG, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def save_entries(entries):
    with open(VIDEO_LOG, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def update_stats(youtube, entries):
    logs = []
    for entry in entries:
        if not entry.get("uploaded") or not entry.get("youtube_video_id"):
            continue
        try:
            response = (
                youtube.videos()
                .list(part="statistics", id=entry["youtube_video_id"])
                .execute()
            )
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

            logs.append(f"📈 {entry['title']}: {views} views, {likes} likes")
            if last_check:
                prev_time = datetime.fromisoformat(last_check)
                hours_elapsed = (datetime.utcnow() - prev_time).total_seconds() / 3600
                growth = (
                    (views - last_views) / hours_elapsed if hours_elapsed > 0 else 0
                )
                if growth > GROWTH_ALERT_THRESHOLD:
                    logs.append(
                        f"🚨 Growth alert: {entry['title']} — {views - last_views} new views in {hours_elapsed:.2f}h — {growth:.1f} views/hr"
                    )
        except Exception as e:
            logs.append(
                f"❌ Failed to fetch stats for {entry.get('youtube_video_id')}: {e}"
            )
    return logs


# Streamlit App
title = "Try This AI Dashboard"
st.set_page_config(page_title=title, layout="wide")
st.title(title)

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Stats", "🖼 Thumbnails", "📤 Upload Queue", "📉 Engagement"]
)

# Tab 1: Stats
with tab1:
    st.header("📊 Update YouTube Stats")
    if st.button("Run Stats Update"):
        with st.spinner("Fetching stats..."):
            youtube = get_authenticated_service()
            entries = load_entries()
            logs = update_stats(youtube, entries)
            save_entries(entries)
        st.success("✅ Stats updated")
        for line in logs:
            st.markdown(f"- {line}")

    st.subheader("📈 Performance Chart")
    entries = load_entries()
    uploaded = [e for e in entries if e.get("uploaded") and "views" in e]
    min_views = st.slider(
        "Minimum views", min_value=0, max_value=10000, value=0, step=100
    )
    filtered = [e for e in uploaded if e["views"] >= min_views]
    if filtered:
        df = pd.DataFrame(filtered)
        st.line_chart(df.set_index("title")[["views", "likes", "comments"]])

    colA, colB = st.columns(2)
    with colA:
        if st.button("▶️ Run Batch Render"):
            st.info("Running batch render...")
            for script in BATCH_RENDER_SCRIPTS:
                path = os.path.join(PIPELINE_DIR, script)
                result = subprocess.run(
                    ["python", path], capture_output=True, text=True
                )
                st.text(f"=== {script} ===\n" + result.stdout + result.stderr)
            st.success("✅ Batch render complete")
    with colB:
        if st.button("📤 Run Batch Upload"):
            st.info("Running batch upload...")
            path = os.path.join(PIPELINE_DIR, BATCH_UPLOAD_SCRIPT)
            result = subprocess.run(["python", path], capture_output=True, text=True)
            st.text("=== upload_next_video.py ===\n" + result.stdout + result.stderr)
            st.success("✅ Batch upload complete")

# Tab 2: Thumbnails
with tab2:
    st.header("🖼 Regenerate Thumbnails")
    if st.button("Generate All Thumbnails"):
        entries = load_entries()
        generate_thumbnails(entries)
        save_entries(entries)
        st.success("✅ Thumbnails regenerated")

    st.subheader("📸 Thumbnail Previews + Scores")
    entries = load_entries()
    for entry in entries:
        thumbs = entry.get("thumbnails", [])
        stats = entry.get("thumbnail_stats", {})
        if thumbs:
            st.markdown(f"**{entry['title']}**")
            cols = st.columns(len(thumbs))
            for i, thumb in enumerate(thumbs):
                with cols[i]:
                    st.image(thumb, width=150)
                    score = stats.get(thumb, {}).get("score", 0.0)
                    reuse = stats.get(thumb, {}).get("reuse", False)
                    st.caption(f"Score: {score:.2f}, Reuse: {reuse}")

# Tab 3: Upload Queue
with tab3:
    st.header("📤 Upload Queue Overview")
    entries = load_entries()
    queue = [e for e in entries if not e.get("uploaded")]
    if queue:
        new_queue = []
        for i, e in enumerate(queue):
            st.markdown(f"### {e['title']}")
            e["title"] = st.text_input(
                f"Edit title {i}", value=e["title"], key=f"title_{i}"
            )
            e["tags"] = st.text_input(
                f"Edit tags {i}", value=", ".join(e.get("tags", [])), key=f"tags_{i}"
            ).split(", ")
            thumbs = e.get("thumbnails", [])
            if thumbs:
                e["thumbnail_used"] = st.selectbox(
                    f"Select thumbnail {i}", thumbs, key=f"thumb_{i}"
                )
            if not st.button(f"❌ Delete {i}"):
                new_queue.append(e)
        if st.button("💾 Save Queue Changes"):
            updated = [e for e in entries if e.get("uploaded")] + new_queue
            save_entries(updated)
            st.success("✅ Upload queue updated")
    else:
        st.info("No pending uploads")

# Tab 4: Engagement
with tab4:
    st.header("📉 Engagement Insights")
    entries = load_entries()
    engaged = [
        e
        for e in entries
        if e.get("uploaded") and all(k in e for k in ["views", "likes", "comments"])
    ]
    if engaged:
        df = pd.DataFrame(engaged)
        df["engagement_rate"] = (df["likes"] + df["comments"]) / df["views"] * 100
        st.dataframe(
            df[["title", "views", "likes", "comments", "engagement_rate"]].sort_values(
                by="engagement_rate", ascending=False
            )
        )
        st.bar_chart(df.set_index("title")["engagement_rate"])
    else:
        st.info("No data for engagement metrics")
