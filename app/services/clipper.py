import ffmpeg
import math
import os
from pathlib import Path

CLIPS_DIR = Path("clips")
CLIPS_DIR.mkdir(exist_ok=True)

def clip_video(input_path: str, output_path: str, start_time: float, end_time: float) -> str:
    """Extract a clip from start_time to end_time without re-encoding."""
    start_str = format_time(start_time)
    duration = end_time - start_time
    
    # Use -map 0 to copy ALL streams (video + audio)
    (
        ffmpeg
        .input(input_path, ss=start_str, t=duration)
        .output(output_path, codec='copy', map='0')
        .overwrite_output()
        .run(quiet=True)
    )
    return output_path

def fit_vertical_blurred_bg(input_path: str, output_path: str) -> str:
    """Fit video into 9:16 (1080x1920) with blurred background fill.
    
    Instead of center-cropping (which cuts content), this:
    1. Creates a blurred, zoomed copy as the background
    2. Scales the original to fit inside 1080x1920 (preserving aspect ratio)
    3. Overlays the sharp original on top of the blurred background
    
    Result: 100% of content visible + premium blurred-fill look.
    """
    inp = ffmpeg.input(input_path)
    
    # Background: scale to fill 1080x1920, then blur heavily
    bg = (
        inp.video
        .filter('scale', 1080, 1920, force_original_aspect_ratio='increase')
        .filter('crop', 1080, 1920)
        .filter('boxblur', 25, 5)
        .filter('setsar', 1)
    )
    
    # Foreground: scale to fit inside 1080x1920 (preserving aspect ratio)
    fg = (
        inp.video
        .filter('scale', 1080, 1920, force_original_aspect_ratio='decrease')
        .filter('setsar', 1)
    )
    
    # Overlay foreground centered on blurred background
    video_out = ffmpeg.overlay(bg, fg, x='(W-w)/2', y='(H-h)/2')
    
    # Get audio stream
    audio = inp.audio
    
    (
        ffmpeg
        .output(video_out, audio, output_path,
                vcodec='libx264', crf=18, acodec='aac',
                preset='medium', movflags='faststart',
                **{'b:a': '192k'})
        .overwrite_output()
        .run(quiet=True)
    )
    return output_path

def format_time(seconds: float) -> str:
    """Convert seconds to HH:MM:SS float format for FFmpeg."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hrs:02d}:{mins:02d}:{secs:06.3f}"


def generate_srt(segments: list[dict], output_path: str, offset: float = 0.0) -> str:
    """Generate SRT subtitle file from transcript segments.
    
    Args:
        segments: List of transcript segments with start/end/text
        output_path: Path to write the SRT file
        offset: Time offset to subtract (so clip starts at 0:00)
    """
    def format_srt_time(seconds: float) -> str:
        seconds = max(0, seconds)
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, seg in enumerate(segments, 1):
            start = seg['start'] - offset
            end = seg['end'] - offset
            if end <= 0:
                continue
            start = max(0, start)
            f.write(f"{i}\n")
            f.write(f"{format_srt_time(start)} --> {format_srt_time(end)}\n")
            f.write(f"{seg['text'].strip()}\n\n")
    
    return output_path


def generate_captions_json(segments: list[dict], output_path: str, offset: float = 0.0) -> str:
    """Generate captions JSON for Remotion (word-level timestamps).
    
    Uses real word-level timestamps from faster-whisper when available,
    falls back to linear estimation when word timestamps are missing.
    
    Format: [{"text": "word", "startMs": 1234, "endMs": 5678}, ...]
    """
    import json
    
    captions = []
    for seg in segments:
        seg_start_ms = max(0, int((seg['start'] - offset) * 1000))
        seg_end_ms = max(0, int((seg['end'] - offset) * 1000))
        if seg_end_ms <= 0:
            continue
        
        # Use real word-level timestamps from Whisper if available
        if seg.get('words') and len(seg['words']) > 0:
            for w in seg['words']:
                w_start = max(0, int((w['start'] - offset) * 1000))
                w_end = max(0, int((w['end'] - offset) * 1000))
                if w_end <= 0:
                    continue
                captions.append({
                    "text": w['word'] + " ",
                    "startMs": w_start,
                    "endMs": w_end,
                })
        else:
            # Fallback: estimate word timing linearly
            words = seg['text'].strip().split()
            if not words:
                continue
            segment_duration_ms = seg_end_ms - seg_start_ms
            word_duration = segment_duration_ms / len(words)
            for j, word in enumerate(words):
                word_start = seg_start_ms + int(j * word_duration)
                word_end = seg_start_ms + int((j + 1) * word_duration)
                captions.append({
                    "text": word + " ",
                    "startMs": word_start,
                    "endMs": word_end,
                })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(captions, f, indent=2)
    
    return output_path


def process_clip(input_path: str, output_dir: Path, clip_idx: int, start_time: float, end_time: float, segments: list[dict] = None) -> dict:
    """"End to end function to create a ready-to-use 9:16 clip with blurred background.
    Generates SRT and Remotion captions JSON."""
    
    raw_clip_path = str(output_dir / f"raw_clip_{clip_idx:02d}.mp4")
    final_clip_path = str(output_dir / f"final_clip_{clip_idx:02d}.mp4")
    
    print(f"Clipping {start_time} to {end_time}...")
    clip_video(input_path, raw_clip_path, start_time, end_time)
    
    print(f"Fitting to 9:16 with blurred background...")
    fit_vertical_blurred_bg(raw_clip_path, final_clip_path)
    
    srt_path = None
    captions_json_path = None
    if segments:
        srt_path = str(output_dir / f"captions_{clip_idx:02d}.srt")
        captions_json_path = str(output_dir / f"captions_{clip_idx:02d}.json")
        generate_srt(segments, srt_path, offset=start_time)
        generate_captions_json(segments, captions_json_path, offset=start_time)
        
    # Cleanup: Remove the intermediary clip
    try:
        if os.path.exists(raw_clip_path):
            os.remove(raw_clip_path)
    except Exception as e:
        print(f"Failed to clean up {raw_clip_path}: {e}")
        
    return {
        "final_video": final_clip_path,
        "srt": srt_path,
        "captions_json": captions_json_path,
    }
