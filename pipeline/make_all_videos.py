import os
from glob import glob
from make_video import render_video

SCRIPT_DIR = "scripts"
VIDEO_DIR = "video"

def get_script_files():
    return glob(os.path.join(SCRIPT_DIR, "*.md"))

def get_video_path(script_path):
    base_name = os.path.splitext(os.path.basename(script_path))[0]
    return os.path.join(VIDEO_DIR, f"{base_name}.mp4")

def main():
    scripts = get_script_files()

    if not scripts:
        print("⚠️ No markdown scripts found in /scripts.")
        return

    for script_path in scripts:
        video_path = get_video_path(script_path)

        if os.path.exists(video_path):
            print(f"✅ Skipping already rendered: {video_path}")
            continue

        try:
            render_video(script_path)
        except Exception as e:
            print(f"❌ Failed to render {script_path}: {e}")

if __name__ == "__main__":
    main()
