---
name: ffmpeg-video-processing
description: How to use FFmpeg for video clipping, cropping to 9:16 vertical, audio extraction, and subtitle burn-in
---

# FFmpeg Video Processing Skill

## Overview

FFmpeg is the backbone of all video/audio processing. It handles clipping, cropping, transcoding, audio extraction, subtitle burn-in, and more. Use `ffmpeg-python` for clean Python integration.

**Docs:** https://ffmpeg.org/documentation.html
**Python wrapper:** https://github.com/kkroening/ffmpeg-python

---

## Installation

```bash
# FFmpeg (system-level)
# Ubuntu/Debian VPS:
sudo apt update && sudo apt install ffmpeg -y

# Python wrapper:
pip install ffmpeg-python
```

---

## Core Operations

### 1. Extract Audio from Video

```python
import ffmpeg

def extract_audio(video_path: str, audio_path: str, sample_rate: int = 16000) -> str:
    """Extract audio from video. Use 16000Hz for Whisper compatibility."""
    (
        ffmpeg
        .input(video_path)
        .output(audio_path, acodec='pcm_s16le', ar=sample_rate, ac=1)
        .overwrite_output()
        .run(quiet=True)
    )
    return audio_path
```

**CLI equivalent:**
```bash
# For Whisper (16KHz WAV mono)
ffmpeg -i input.mp4 -ar 16000 -ac 1 -acodec pcm_s16le audio.wav -y

# For general use (MP3)
ffmpeg -i input.mp4 -vn -acodec libmp3lame -q:a 2 audio.mp3 -y
```

### 2. Clip a Segment from Video

```python
def clip_video(input_path: str, output_path: str, start_time: str, end_time: str) -> str:
    """Extract a clip from start_time to end_time.
    
    Times in format: "HH:MM:SS" or seconds as float.
    """
    (
        ffmpeg
        .input(input_path, ss=start_time, to=end_time)
        .output(output_path, codec='copy')  # No re-encoding = fast
        .overwrite_output()
        .run(quiet=True)
    )
    return output_path
```

**CLI equivalent:**
```bash
ffmpeg -i input.mp4 -ss 00:02:10 -to 00:02:45 -c copy clip.mp4
```

### 3. Crop to Vertical 9:16 (Center Crop)

```python
def crop_vertical(input_path: str, output_path: str) -> str:
    """Crop horizontal video to 9:16 vertical (center crop)."""
    probe = ffmpeg.probe(input_path)
    video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    width = int(video_stream['width'])
    height = int(video_stream['height'])
    
    # Calculate crop dimensions for 9:16
    new_width = int(height * 9 / 16)
    x_offset = (width - new_width) // 2  # Center crop
    
    (
        ffmpeg
        .input(input_path)
        .filter('crop', new_width, height, x_offset, 0)
        .output(output_path, vcodec='libx264', crf=18, acodec='aac')
        .overwrite_output()
        .run(quiet=True)
    )
    return output_path
```

**CLI equivalent:**
```bash
# Center crop to 9:16
ffmpeg -i input.mp4 -vf "crop=ih*9/16:ih" -c:a copy output.mp4
```

### 4. Scale to Exact Resolution (1080x1920)

```python
def scale_to_shorts(input_path: str, output_path: str, 
                     width: int = 1080, height: int = 1920) -> str:
    """Scale video to exact Shorts resolution."""
    (
        ffmpeg
        .input(input_path)
        .filter('scale', width, height)
        .output(output_path, vcodec='libx264', crf=18, acodec='aac')
        .overwrite_output()
        .run(quiet=True)
    )
    return output_path
```

### 5. Clip + Crop in One Command (Efficient)

```python
def clip_and_crop_vertical(input_path: str, output_path: str,
                            start: str, end: str) -> str:
    """Extract a clip AND crop to 9:16 in a single pass."""
    probe = ffmpeg.probe(input_path)
    video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    width = int(video_stream['width'])
    height = int(video_stream['height'])
    new_width = int(height * 9 / 16)
    x_offset = (width - new_width) // 2
    
    (
        ffmpeg
        .input(input_path, ss=start, to=end)
        .filter('crop', new_width, height, x_offset, 0)
        .filter('scale', 1080, 1920)
        .output(output_path, vcodec='libx264', crf=18, acodec='aac', 
                preset='medium', movflags='faststart')
        .overwrite_output()
        .run(quiet=True)
    )
    return output_path
```

### 6. Burn Subtitles into Video

```python
def burn_subtitles(input_path: str, srt_path: str, output_path: str) -> str:
    """Burn SRT subtitles into video with styling."""
    style = (
        "FontName=Arial Bold,"
        "FontSize=24,"
        "PrimaryColour=&H00FFFFFF,"      # White text
        "OutlineColour=&H00000000,"      # Black outline
        "BackColour=&H80000000,"         # Semi-transparent background
        "Outline=2,"
        "Shadow=1,"
        "Alignment=10,"                  # Center-top of bottom area
        "MarginV=80"
    )
    
    (
        ffmpeg
        .input(input_path)
        .output(output_path, vf=f"subtitles={srt_path}:force_style='{style}'",
                vcodec='libx264', crf=18, acodec='aac')
        .overwrite_output()
        .run(quiet=True)
    )
    return output_path
```

### 7. Get Video Duration

```python
def get_duration(video_path: str) -> float:
    """Get video duration in seconds."""
    probe = ffmpeg.probe(video_path)
    return float(probe['format']['duration'])
```

---

## SRT File Generation

```python
def generate_srt(segments: list[dict], output_path: str) -> str:
    """Generate SRT subtitle file from transcript segments.
    
    segments: [{"start": 0.0, "end": 2.5, "text": "Hello world"}, ...]
    """
    def format_time(seconds: float) -> str:
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, seg in enumerate(segments, 1):
            f.write(f"{i}\n")
            f.write(f"{format_time(seg['start'])} --> {format_time(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")
    
    return output_path
```

---

## VPS Performance Tips

- Use `-preset ultrafast` for speed over compression on VPS
- Use `-crf 23` (default) for good quality/size balance
- Add `-movflags +faststart` for streaming-optimized MP4
- Use `-threads 0` to use all available CPU cores
- For batch jobs, process sequentially to avoid OOM on low-RAM VPS
