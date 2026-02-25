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

def full_transcribe_pipeline(video_path: str, video_id: str) -> list[dict]:
    """Extract audio, transcribe, and save transcript."""
    audio_path = str(TEMP_DIR / f"{video_id}.wav")
    
    print(f"Extracting audio for {video_id}...")
    extract_audio(video_path, audio_path)
    
    print(f"Transcribing {video_id} using faster-whisper...")
    segments = transcribe_audio(audio_path)
    
    # Save the structured transcript next to where yt-dlp sub downloads would go
    transcript_path = SUBTITLES_DIR / f"{video_id}_transcript.json"
    with open(transcript_path, "w", encoding='utf-8') as f:
        json.dump(segments, f, indent=2)
        
    return segments
