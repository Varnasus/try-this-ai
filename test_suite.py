import os
import unittest
from pathlib import Path
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv
import moviepy_conf  # Import MoviePy configuration
from pipeline.text_to_speech import run_tts
from pipeline.make_video import render_video
from pipeline.generate_metadata import generate_video_metadata

# Load environment variables
load_dotenv()

class TestSystem(unittest.TestCase):
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
        img = Image.new('RGB', (1920, 1080), color='black')
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
    
    def test_01_environment_variables(self):
        """Test if all required environment variables are set"""
        required_vars = [
            "OPENAI_API_KEY",
            "ELEVENLABS_API_KEY",
            "YOUTUBE_API_KEY",
            "YT_REFRESH_TOKEN",
            "YT_CLIENT_ID",
            "YT_CLIENT_SECRET"
        ]
        
        for var in required_vars:
            self.assertIsNotNone(
                os.getenv(var),
                f"Environment variable {var} is not set"
            )
    
    def test_02_openai_client(self):
        """Test OpenAI client functionality"""
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Say 'test'"}
                ],
                max_tokens=5
            )
            self.assertIsNotNone(response.choices[0].message.content)
        except Exception as e:
            self.fail(f"OpenAI client test failed: {str(e)}")
    
    def test_03_text_to_speech(self):
        """Test text-to-speech functionality"""
        output_path = self.test_dir / "audio" / "test_audio.mp3"
        
        try:
            run_tts(self.test_script, output_path=str(output_path))
            self.assertTrue(
                output_path.exists(),
                "Audio file was not created"
            )
            self.assertGreater(
                output_path.stat().st_size,
                0,
                "Audio file is empty"
            )
        except Exception as e:
            self.fail(f"Text-to-speech test failed: {str(e)}")
    
    def test_04_metadata_generation(self):
        """Test metadata generation"""
        try:
            metadata = generate_video_metadata(self.test_script)
            self.assertIsInstance(metadata, dict)
            self.assertIn("title", metadata)
            self.assertIn("description", metadata)
            self.assertIn("tags", metadata)
            
            # Additional validation
            self.assertLessEqual(len(metadata["title"]), 100, "Title is too long")
            self.assertIsInstance(metadata["tags"], list, "Tags should be a list")
        except Exception as e:
            self.fail(f"Metadata generation test failed: {str(e)}")
    
    def test_05_video_generation(self):
        """Test video generation pipeline"""
        try:
            render_video(
                str(self.script_path),
                background_img=str(self.background_path)
            )
            
            output_path = Path("video") / "test_script.mp4"
            self.assertTrue(
                output_path.exists(),
                "Video file was not created"
            )
            self.assertGreater(
                output_path.stat().st_size,
                0,
                "Video file is empty"
            )
        except Exception as e:
            self.fail(f"Video generation test failed: {str(e)}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test files"""
        import shutil
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)

if __name__ == "__main__":
    unittest.main() 