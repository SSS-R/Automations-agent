import os
import subprocess
import sys

# Add parent dir to path so we can import transcriber
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from app.services.transcriber import transcribe_audio

def get_audio_duration(file_path: str) -> float:
    """Get audio duration in seconds using ffprobe."""
    if not os.path.exists(file_path):
        return 0.0
    command = [
        "ffprobe", 
        "-v", "error", 
        "-show_entries", "format=duration", 
        "-of", "default=noprint_wrappers=1:nokey=1", 
        file_path
    ]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting duration for {file_path}: {e}")
        return 0.0

def generate_caption_pages(segments: list[dict], max_words_per_page: int = 4) -> list[dict]:
    """Converts faster-whisper segments into Remotion CaptionPages format."""
    pages = []
    
    for segment in segments:
        words = segment.get("words", [])
        if not words:
            continue
            
        current_page = []
        for word in words:
            current_page.append({
                "text": word["word"],
                "startMs": int(word["start"] * 1000),
                "endMs": int(word["end"] * 1000)
            })
            
            if len(current_page) >= max_words_per_page:
                pages.append({
                    "startMs": current_page[0]["startMs"],
                    "endMs": current_page[-1]["endMs"],
                    "tokens": current_page
                })
                current_page = []
                
        if current_page: # remaining words
            pages.append({
                "startMs": current_page[0]["startMs"],
                "endMs": current_page[-1]["endMs"],
                "tokens": current_page
            })
            
    return pages

def process_audio_for_scene(audio_path: str, fps: int = 30) -> tuple[int, list[dict]]:
    """Returns total duration in frames and caption pages."""
    duration_sec = get_audio_duration(audio_path)
    buffer_sec = 0.5 # 0.5s buffer so text doesn't end abruptly
    duration_frames = int((duration_sec + buffer_sec) * fps)
    
    print(f"Transcribing: {audio_path}")
    segments = transcribe_audio(audio_path)
    caption_pages = generate_caption_pages(segments)
    
    return duration_frames, caption_pages
