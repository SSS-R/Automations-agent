import yt_dlp
import os
import json
from pathlib import Path

VIDEOS_DIR = Path("videos")
TEMP_DIR = Path("temp")
SUBTITLES_DIR = Path("subtitles")

VIDEOS_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
SUBTITLES_DIR.mkdir(exist_ok=True)

def download_video(url: str) -> dict:
    """Download the best quality mp4 video and extract metadata."""
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'{VIDEOS_DIR}/%(id)s.%(ext)s',
        'writeinfojson': True,
        'writethumbnail': True,
        'merge_output_format': 'mp4',
        'quiet': False,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        metadata = {
            'id': info.get('id'),
            'title': info.get('title'),
            'duration': info.get('duration'),
            'channel': info.get('channel') or info.get('uploader'),
            'filepath': ydl.prepare_filename(info),
            'url': url
        }
        
        # Save simplified metadata
        metadata_path = VIDEOS_DIR / f"{metadata['id']}_summary.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
            
        return metadata

def fetch_existing_transcript(url: str) -> dict | None:
    """Attempt to download existing auto-captions/subtitles."""
    ydl_opts = {
        'writeautomaticsub': True,
        'writesubtitles': True,
        'subtitleslangs': ['en'],
        'skip_download': True,
        'outtmpl': f'{SUBTITLES_DIR}/%(id)s',
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            video_id = info.get('id')
            
            # Subtitles are usually saved as .en.vtt or similar
            # We'll check the directory for the generated file
            for file in os.listdir(SUBTITLES_DIR):
                if file.startswith(video_id) and (file.endswith('.vtt') or file.endswith('.srt')):
                    return {
                        "status": "found",
                        "path": str(SUBTITLES_DIR / file)
                    }
                    
            return None
        except Exception as e:
            print(f"Error fetching existing transcript: {e}")
            return None
