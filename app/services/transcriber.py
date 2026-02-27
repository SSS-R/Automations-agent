import json
import hashlib
from pathlib import Path
from faster_whisper import WhisperModel
import subprocess

TEMP_DIR = Path("temp")
CACHE_DIR = Path("temp/cache")
SUBTITLES_DIR = Path("subtitles")

TEMP_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def extract_audio(video_path: str, output_path: str) -> str:
    """Extract audio from video file to wav format for faster-whisper."""
    command = [
        "ffmpeg",
        "-i", video_path,
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        "-y", # Overwrite output file
        output_path
    ]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path

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

def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"

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


def transcribe_audio(audio_path: str, model_size: str = "small") -> list[dict]:
    """Transcribe audio file and return segments with timestamps."""
    cached = get_cached_transcript(audio_path)
    if cached:
        print("Using cached transcript")
        return cached

    # Faster-whisper handles model downloading automatically if missing
    # int8 is best for CPU, and small model strikes balance of speed/accuracy
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        language="en",
        word_timestamps=True,
        vad_filter=True,
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
    
    save_transcript_cache(audio_path, result)
    return result

def full_transcribe_pipeline(video_path: str, video_id: str, existing_sub_path: str = None) -> list[dict]:
    """Extract audio, transcribe, and save transcript.
    
    If existing_sub_path is provided (from Tier 1 platform subtitle download),
    parse it directly instead of running Whisper — saves ~5 min per video.
    """
    # Tier 1: Use existing platform subtitles if available
    if existing_sub_path:
        print(f"♻️ Using existing platform subtitles: {existing_sub_path}")
        segments = parse_subtitle_file(existing_sub_path)
        if segments:
            transcript_path = SUBTITLES_DIR / f"{video_id}_transcript.json"
            with open(transcript_path, "w", encoding='utf-8') as f:
                json.dump(segments, f, indent=2)
            return segments
        print("⚠️ Platform subtitle parsing failed, falling back to Whisper...")

    # Tier 2: Local faster-whisper transcription
    audio_path = str(TEMP_DIR / f"{video_id}.wav")
    
    print(f"Extracting audio for {video_id}...")
    extract_audio(video_path, audio_path)
    
    print(f"Transcribing {video_id} using faster-whisper...")
    segments = transcribe_audio(audio_path)
    
    transcript_path = SUBTITLES_DIR / f"{video_id}_transcript.json"
    with open(transcript_path, "w", encoding='utf-8') as f:
        json.dump(segments, f, indent=2)
        
    return segments


def parse_subtitle_file(filepath: str) -> list[dict] | None:
    """Parse a VTT or SRT subtitle file into segment format.
    
    Returns the same format as Whisper output:
    [{"start": 0.0, "end": 5.2, "text": "...", "words": []}]
    """
    try:
        if filepath.endswith('.vtt'):
            return parse_vtt_file(filepath)
        elif filepath.endswith('.srt'):
            return parse_srt_file(filepath)
        return None
    except Exception as e:
        print(f"Error parsing subtitle file: {e}")
        return None


def parse_vtt_file(filepath: str) -> list[dict]:
    """Parse WebVTT subtitle file into segments."""
    import re
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    segments = []
    # VTT timestamp pattern: 00:00:01.234 --> 00:00:05.678
    pattern = re.compile(
        r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})\s*\n(.*?)(?=\n\n|\n\d{2}:\d{2}|\Z)',
        re.DOTALL
    )
    
    for match in pattern.finditer(content):
        start = _parse_vtt_timestamp(match.group(1))
        end = _parse_vtt_timestamp(match.group(2))
        text = match.group(3).strip()
        
        # Remove VTT formatting tags like <c> and position tags
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\n', ' ', text).strip()
        
        if text and end > start:
            segments.append({
                "start": round(start, 2),
                "end": round(end, 2),
                "text": text,
                "words": []  # Platform subs don't have word-level timestamps
            })
    
    # Deduplicate overlapping segments (YouTube auto-captions often repeat)
    if segments:
        deduped = [segments[0]]
        for seg in segments[1:]:
            prev = deduped[-1]
            # Skip if this segment's text is contained in the previous one
            if seg['text'] in prev['text'] or prev['text'] in seg['text']:
                # Keep the longer one with the wider time range
                if len(seg['text']) > len(prev['text']):
                    deduped[-1] = seg
            else:
                deduped.append(seg)
        segments = deduped
    
    return segments


def parse_srt_file(filepath: str) -> list[dict]:
    """Parse SRT subtitle file into segments."""
    import re
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    segments = []
    # SRT pattern: index\n00:00:01,234 --> 00:00:05,678\ntext
    blocks = re.split(r'\n\n+', content.strip())
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        # Second line should be timestamps
        time_match = re.match(
            r'(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})',
            lines[1]
        )
        if not time_match:
            continue
        
        start = _parse_srt_timestamp(time_match.group(1))
        end = _parse_srt_timestamp(time_match.group(2))
        text = ' '.join(lines[2:]).strip()
        
        if text and end > start:
            segments.append({
                "start": round(start, 2),
                "end": round(end, 2),
                "text": text,
                "words": []
            })
    
    return segments


def _parse_vtt_timestamp(ts: str) -> float:
    """Convert VTT timestamp (HH:MM:SS.mmm) to seconds."""
    parts = ts.split(':')
    h, m = int(parts[0]), int(parts[1])
    s = float(parts[2])
    return h * 3600 + m * 60 + s


def _parse_srt_timestamp(ts: str) -> float:
    """Convert SRT timestamp (HH:MM:SS,mmm) to seconds."""
    ts = ts.replace(',', '.')
    return _parse_vtt_timestamp(ts)
