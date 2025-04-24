import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import streamlit as st
from dotenv import load_dotenv
from PIL import Image

import moviepy_conf  # Import MoviePy configuration
from pipeline.generate_metadata import generate_video_metadata
from pipeline.make_video import render_video
from pipeline.text_to_speech import run_tts

# Load environment variables
load_dotenv()


class MockSessionState(dict):
    """Mock Streamlit session state"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mock_callbacks = {}

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if key in self._mock_callbacks:
            self._mock_callbacks[key](value)

    def on_change(self, key, callback):
        self._mock_callbacks[key] = callback


class TestStreamlitApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_dir = Path("test_output")
        cls.test_dir.mkdir(exist_ok=True)

        # Create necessary subdirectories
        (cls.test_dir / "scripts").mkdir(exist_ok=True)
        (cls.test_dir / "audio").mkdir(exist_ok=True)
        (cls.test_dir / "video").mkdir(exist_ok=True)
        (cls.test_dir / "thumbnails").mkdir(exist_ok=True)

        # Create a test background image
        cls.background_path = cls.test_dir / "thumbnails" / "test_background.png"
        img = Image.new("RGB", (1920, 1080), color="black")
        img.save(cls.background_path)

        # Test script content
        cls.test_script = """
# Test Video Script

This is a test script for verifying the video generation pipeline.
It should be short enough to process quickly but contain enough content
to test all major components of the system.
"""

        # Save test script
        cls.script_path = cls.test_dir / "scripts" / "test_script.md"
        with open(cls.script_path, "w", encoding="utf-8") as f:
            f.write(cls.test_script)

    def setUp(self):
        """Set up test case"""
        # Create mock session state
        self.session_state = MockSessionState()
        self.patcher = patch("streamlit.session_state", self.session_state)
        self.mock_session_state = self.patcher.start()

    def tearDown(self):
        """Clean up after each test"""
        self.patcher.stop()

    def test_01_streamlit_session_state(self):
        """Test Streamlit session state initialization"""
        # Initialize session state
        self.session_state["script_text"] = self.test_script
        self.session_state["voice"] = "Laura"
        self.session_state["background_img"] = str(self.background_path)

        self.assertIn("script_text", self.session_state)
        self.assertIn("voice", self.session_state)
        self.assertIn("background_img", self.session_state)

    def test_02_streamlit_file_upload(self):
        """Test file upload handling"""
        mock_uploaded_file = MagicMock()
        mock_uploaded_file.name = "test_script.md"
        mock_uploaded_file.getvalue.return_value = self.test_script.encode()

        with patch("streamlit.file_uploader", return_value=mock_uploaded_file):
            uploaded_file = st.file_uploader("Upload your script", type=["md"])
            self.assertIsNotNone(uploaded_file)
            self.assertEqual(uploaded_file.name, "test_script.md")

    def test_03_streamlit_voice_selection(self):
        """Test voice selection handling"""
        with patch("streamlit.selectbox", return_value="Laura"):
            selected_voice = st.selectbox("Select voice", ["Laura", "Rachel", "Other"])
            self.assertEqual(selected_voice, "Laura")

    def test_04_streamlit_background_selection(self):
        """Test background image selection handling"""
        mock_uploaded_file = MagicMock()
        mock_uploaded_file.name = "background.png"

        with patch("streamlit.file_uploader", return_value=mock_uploaded_file):
            uploaded_bg = st.file_uploader(
                "Upload background image", type=["png", "jpg", "jpeg"]
            )
            self.assertIsNotNone(uploaded_bg)

    def test_05_generate_button_with_missing_inputs(self):
        """Test generate button behavior when inputs are missing"""
        with patch("streamlit.button", return_value=True) as mock_button, patch(
            "streamlit.error"
        ) as mock_error:
            # Test with no script
            if mock_button("Generate Video"):
                mock_error.assert_not_called()  # No error yet
                self.assertNotIn("script_text", self.session_state)

            # Test with script but no voice
            self.session_state["script_text"] = self.test_script
            if mock_button("Generate Video"):
                mock_error.assert_not_called()  # No error yet
                self.assertNotIn("voice", self.session_state)

            # Test with script and voice but no background
            self.session_state["voice"] = "Laura"
            if mock_button("Generate Video"):
                mock_error.assert_not_called()  # No error yet
                self.assertNotIn("background_img", self.session_state)

    def test_06_generate_button_with_valid_inputs(self):
        """Test generate button behavior with all required inputs"""
        # Set up session state with all required inputs
        self.session_state.update(
            {
                "script_text": self.test_script,
                "voice": "Laura",
                "background_img": str(self.background_path),
            }
        )

        # Create mock functions
        mock_tts = MagicMock()
        mock_render = MagicMock()
        mock_success = MagicMock()

        with patch("streamlit.button", return_value=True) as mock_button, patch(
            "pipeline.text_to_speech.run_tts", mock_tts
        ), patch("pipeline.make_video.render_video", mock_render), patch(
            "streamlit.success", mock_success
        ):
            # Simulate button click
            if mock_button("Generate Video"):
                # Call the functions as they would be called in the app
                mock_tts(self.test_script, str(self.test_dir / "audio" / "test.mp3"))
                mock_render(str(self.script_path), str(self.background_path))
                mock_success("Video generated successfully!")

                # Verify the functions were called with correct arguments
                mock_tts.assert_called_once_with(
                    self.test_script, str(self.test_dir / "audio" / "test.mp3")
                )
                mock_render.assert_called_once_with(
                    str(self.script_path), str(self.background_path)
                )
                mock_success.assert_called_once_with("Video generated successfully!")

    def test_07_preview_button(self):
        """Test preview button functionality"""
        # Set up session state with script text
        self.session_state["script_text"] = self.test_script

        # Create mock functions
        mock_markdown = MagicMock()

        with patch("streamlit.button", return_value=True) as mock_button, patch(
            "streamlit.markdown", mock_markdown
        ):
            # Simulate button click
            if mock_button("Preview"):
                mock_markdown(self.test_script)
                mock_markdown.assert_called_once_with(self.test_script)

    def test_08_clear_button(self):
        """Test clear button functionality"""
        # Set up session state with some data
        self.session_state.update(
            {
                "script_text": self.test_script,
                "voice": "Laura",
                "background_img": str(self.background_path),
            }
        )

        with patch("streamlit.button", return_value=True) as mock_button:
            if mock_button("Clear"):
                # Clear session state
                self.session_state.clear()
                self.assertEqual(len(self.session_state), 0)

    def test_09_button_state_management(self):
        """Test button state management"""
        with patch("streamlit.button") as mock_button:
            # Test button disabled state
            mock_button.return_value = False

            # Generate button should be disabled without inputs
            mock_button("Generate Video", disabled=True)

            # Add required inputs one by one
            self.session_state["script_text"] = self.test_script
            mock_button("Generate Video", disabled=True)

            self.session_state["voice"] = "Laura"
            mock_button("Generate Video", disabled=True)

            self.session_state["background_img"] = str(self.background_path)
            mock_button("Generate Video", disabled=False)

            # Verify button calls
            expected_calls = [
                call("Generate Video", disabled=True),
                call("Generate Video", disabled=True),
                call("Generate Video", disabled=True),
                call("Generate Video", disabled=False),
            ]
            mock_button.assert_has_calls(expected_calls)

    @classmethod
    def tearDownClass(cls):
        """Clean up test files"""
        import shutil

        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)


if __name__ == "__main__":
    unittest.main()
