---
name: faster-whisper-transcription
description: How to use faster-whisper for free local speech-to-text transcription with word-level timestamps
---

# faster-whisper Local Transcription Skill

## Overview

`faster-whisper` is a reimplementation of OpenAI's Whisper model using CTranslate2, making it **4x faster** and using **less memory** than the original. It runs entirely locally — **no API costs**.

**GitHub:** https://github.com/SYSTRAN/faster-whisper
**License:** MIT (free)

---

## Installation

```bash
# CPU only
pip install faster-whisper

# With GPU support (NVIDIA CUDA)
pip install faster-whisper[cuda]
```

> On a $5 VPS (CPU only), use the `small` model. It transcribes a 30-min video in ~5-8 minutes.

---

## Python API

### Basic Transcription

```python
from faster_whisper import WhisperModel

def transcribe_audio(audio_path: str, model_size: str = "small") -> list[dict]:
    """Transcribe audio file and return segments with timestamps.
    
    Model sizes: tiny, base, small, medium, large-v3
    - tiny:   fastest, lowest accuracy (~1 GB RAM)
    - small:  good balance for VPS (~2 GB RAM) ← RECOMMENDED
    - medium: better accuracy (~5 GB RAM)
    - large:  best accuracy (~10 GB RAM, needs GPU)
    """
    
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        language="en",           # Set language or None for auto-detect
        word_timestamps=True,    # Enable word-level timing
        vad_filter=True,         # Filter out silence (faster)
    )
    
    result = []
    for segment in segments:
        result.append({
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip(),
            "words": [
                {
                    "word": word.word.strip(),
                    "start": round(word.start, 2),
                    "end": round(word.end, 2),
                    "probability": round(word.probability, 3),
                }
                for word in (segment.words or [])
            ]
        })
    
    return result
```

### Transcription with Caching

```python
import json
import hashlib
from pathlib import Path

CACHE_DIR = Path("./cache/transcripts")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def get_cached_transcript(audio_path: str) -> list[dict] | None:
    """Check if transcript is already cached."""
    cache_key = hashlib.md5(Path(audio_path).read_bytes()[:1024*1024]).hexdigest()
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    return None

def save_transcript_cache(audio_path: str, transcript: list[dict]):
    """Save transcript to cache."""
    cache_key = hashlib.md5(Path(audio_path).read_bytes()[:1024*1024]).hexdigest()
    cache_file = CACHE_DIR / f"{cache_key}.json"
    cache_file.write_text(json.dumps(transcript, indent=2))

def transcribe_with_cache(audio_path: str, model_size: str = "small") -> list[dict]:
    """Transcribe with caching to avoid re-processing."""
    cached = get_cached_transcript(audio_path)
    if cached:
        print("Using cached transcript")
        return cached
    
    transcript = transcribe_audio(audio_path, model_size)
    save_transcript_cache(audio_path, transcript)
    return transcript
```

### Format Transcript for LLM

```python
def format_for_llm(segments: list[dict]) -> str:
    """Format transcript for LLM highlight detection.
    
    Returns a compact string with timestamps that the LLM can analyze.
    """
    lines = []
    for seg in segments:
        start = format_timestamp(seg['start'])
        end = format_timestamp(seg['end'])
        lines.append(f"[{start} → {end}] {seg['text']}")
    return "\n".join(lines)

def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"
```

---

## Model Selection Guide

| Model | RAM Needed | Speed (30 min audio) | Accuracy | Best For |
|-------|-----------|---------------------|----------|----------|
| `tiny` | ~1 GB | ~1 min | Fair | Quick tests |
| `base` | ~1 GB | ~2 min | Good | Low-RAM VPS |
| `small` | ~2 GB | ~5 min | **Great** | **$5 VPS (recommended)** |
| `medium` | ~5 GB | ~10 min | Excellent | 8GB+ VPS |
| `large-v3` | ~10 GB | ~20 min | Best | GPU only |

> For a **$5 VPS with 4GB RAM**, use the `small` model with `compute_type="int8"`. It gives excellent accuracy while staying within memory limits.

---

## VPS Setup

```bash
# Install on Ubuntu VPS
sudo apt update && sudo apt install -y python3-pip ffmpeg
pip install faster-whisper

# First run downloads the model (~500MB for 'small')
# Models are cached in ~/.cache/huggingface/
```

---

## Cost: $0

Unlike OpenAI Whisper API ($0.006/min), faster-whisper is completely free. A 30-minute video:
- **API cost:** $0.18
- **faster-whisper:** $0.00
- **At 10 videos/day:** saves **$54/month**
