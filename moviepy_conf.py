import os
from moviepy.config import change_settings

# Configure MoviePy to use ImageMagick
IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
change_settings({
    "IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY,
    "FFMPEG_BINARY": os.getenv('FFMPEG_BINARY', 'ffmpeg')  # Also ensure FFMPEG is configured
}) 