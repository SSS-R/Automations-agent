---
name: yt-dlp-video-download
description: How to download videos from YouTube and other platforms using yt-dlp with Python
---

# yt-dlp Video Download Skill

## Overview

`yt-dlp` is the most powerful and maintained video downloader. It supports **1000+ sites** including YouTube, TikTok, Instagram, Twitter/X, Facebook, and more. It's a fork of `youtube-dl` with many improvements.

**GitHub:** https://github.com/yt-dlp/yt-dlp
**License:** Unlicense (free)

---

## Installation

```bash
pip install yt-dlp
```

---

## Python API Usage

### Basic Download

```python
import yt_dlp

def download_video(url: str, output_dir: str = "./videos") -> dict:
    """Download a video and return metadata."""
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'writeinfojson': True,        # Save metadata JSON
        'writethumbnail': True,       # Download thumbnail
        'merge_output_format': 'mp4', # Always output MP4
        'quiet': False,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return {
            'title': info.get('title'),
            'duration': info.get('duration'),    # seconds
            'channel': info.get('channel') or info.get('uploader'),
            'view_count': info.get('view_count'),
            'filepath': ydl.prepare_filename(info),
            'description': info.get('description'),
            'upload_date': info.get('upload_date'),
        }
```

### Extract Info Only (No Download)

```python
def get_video_info(url: str) -> dict:
    """Get video metadata without downloading."""
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            'title': info.get('title'),
            'duration': info.get('duration'),
            'channel': info.get('channel'),
            'formats': len(info.get('formats', [])),
        }
```

### Download Audio Only (for Transcription)

```python
def download_audio_only(url: str, output_dir: str = "./temp") -> str:
    """Download just the audio track as MP3."""
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # yt-dlp changes extension after post-processing
        return f"{output_dir}/{info['title']}.mp3"
```

### URL Detection (Multi-Platform)

```python
import re

SUPPORTED_PATTERNS = {
    'youtube':   r'(youtube\.com|youtu\.be)',
    'tiktok':    r'tiktok\.com',
    'instagram': r'instagram\.com',
    'twitter':   r'(twitter\.com|x\.com)',
    'facebook':  r'facebook\.com',
}

def detect_platform(url: str) -> str | None:
    """Detect which platform a URL belongs to."""
    for platform, pattern in SUPPORTED_PATTERNS.items():
        if re.search(pattern, url):
            return platform
    return None

def is_supported_url(url: str) -> bool:
    """Check if URL is from a supported platform."""
    return detect_platform(url) is not None
```

---

## CLI Usage (Quick Reference)

```bash
# Best quality MP4
yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best" -o "videos/%(title)s.%(ext)s" URL

# Audio only (MP3)
yt-dlp -x --audio-format mp3 -o "temp/%(title)s.%(ext)s" URL

# With metadata + thumbnail
yt-dlp --write-info-json --write-thumbnail -o "videos/%(title)s.%(ext)s" URL

# List available formats
yt-dlp -F URL

# Download specific format
yt-dlp -f 137+140 URL
```

---

## VPS Considerations

- yt-dlp downloads can be bandwidth-heavy — watch VPS transfer limits
- Use `--limit-rate 5M` to throttle download speed if needed
- Cache downloaded videos to avoid re-downloading
- Clean up source videos after processing to save storage
