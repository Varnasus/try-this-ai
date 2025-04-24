import os
import sys
from pathlib import Path

import streamlit as st
from PIL import Image

from config import Config, Environment
from pipeline.make_video import render_video
from pipeline.text_to_speech import run_tts

# Check environment before importing other modules
try:
    from scripts.check_environment import check_environment

    if not check_environment():
        st.error("⚠️ Environment check failed. Please check the console for details.")
        st.stop()
except ImportError as e:
    st.error(f"⚠️ Could not perform environment check: {e}")
    st.stop()

# Initialize configuration
Config.load_config(
    Environment.PRODUCTION
)  # or Environment.DEVELOPMENT based on your needs

# Get configuration values
APP_NAME = Config.get("app.name")
MAX_SCRIPT_SIZE = Config.get("files.max_size.script")
ALLOWED_SCRIPT_EXTENSIONS = Config.get("files.allowed_extensions.scripts")
ALLOWED_IMAGE_EXTENSIONS = Config.get("files.allowed_extensions.images")

# Initialize session state if not exists
if "script_text" not in st.session_state:
    st.session_state["script_text"] = ""
if "voice" not in st.session_state:
    st.session_state["voice"] = "Laura"
if "background_img" not in st.session_state:
    st.session_state["background_img"] = None

st.title(APP_NAME)

# Script input with configuration-based validation
script_file = st.file_uploader("Upload your script", type=ALLOWED_SCRIPT_EXTENSIONS)
if script_file:
    if script_file.size > MAX_SCRIPT_SIZE:
        st.error(
            f"Script file too large. Maximum size is {MAX_SCRIPT_SIZE/1024/1024:.1f}MB"
        )
    else:
        script_content = script_file.getvalue().decode()
        st.session_state["script_text"] = script_content

# Voice selection
voice_options = ["Laura", "Rachel", "Other"]
selected_voice = st.selectbox("Select voice", voice_options)
st.session_state["voice"] = selected_voice

# Background image upload
background_file = st.file_uploader(
    "Upload background image", type=["png", "jpg", "jpeg"]
)
if background_file:
    # Save the uploaded background image
    os.makedirs("thumbnails", exist_ok=True)
    bg_path = os.path.join("thumbnails", background_file.name)
    with open(bg_path, "wb") as f:
        f.write(background_file.getbuffer())
    st.session_state["background_img"] = bg_path

# Preview button
if st.button("Preview"):
    if st.session_state.get("script_text"):
        st.markdown(st.session_state["script_text"])
    else:
        st.error("Please upload a script first.")

# Generate button
generate_button = st.button(
    "Generate Video",
    disabled=not all(
        [
            st.session_state.get("script_text"),
            st.session_state.get("voice"),
            st.session_state.get("background_img"),
        ]
    ),
)

if generate_button:
    if all(
        [
            st.session_state.get("script_text"),
            st.session_state.get("voice"),
            st.session_state.get("background_img"),
        ]
    ):
        with st.spinner("Generating video..."):
            # Save script to file
            os.makedirs("scripts", exist_ok=True)
            script_path = os.path.join("scripts", "temp_script.md")
            with open(script_path, "w") as f:
                f.write(st.session_state["script_text"])

            # Generate audio
            os.makedirs("audio", exist_ok=True)
            audio_path = os.path.join("audio", "temp.mp3")
            run_tts(st.session_state["script_text"], audio_path)

            # Generate video
            render_video(script_path, st.session_state["background_img"])

            st.success("Video generated successfully!")
    else:
        st.error(
            "Please provide all required inputs: script, voice, and background image."
        )

# Clear button
if st.button("Clear"):
    st.session_state.clear()
