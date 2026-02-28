import os
import sys

# Add parent path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app/services')))

from app.services.faceless.audio_sync import process_audio_for_scene
from app.services.transcriber import extract_audio
import json

if __name__ == "__main__":
    video_path = os.path.abspath("remotion-editor/public/temp_vid_3536ffe3.mp4")
    audio_path = os.path.abspath("temp/dummy_audio.wav")
    
    print("Extracting audio...")
    extract_audio(video_path, audio_path)
    
    print("Processing audio for scene...")
    duration, pages = process_audio_for_scene(audio_path)
    
    print(f"Duration frames: {duration}")
    print("First page:")
    print(json.dumps(pages[0:1], indent=2))
