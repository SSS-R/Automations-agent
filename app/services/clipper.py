import ffmpeg
import math
from pathlib import Path

CLIPS_DIR = Path("clips")
CLIPS_DIR.mkdir(exist_ok=True)

def clip_video(input_path: str, output_path: str, start_time: float, end_time: float) -> str:
    """Extract a clip from start_time to end_time without re-encoding."""
    # Convert seconds to format expected by ffmpeg
    start_str = format_time(start_time)
    end_str = format_time(end_time)
    
    (
        ffmpeg
        .input(input_path, ss=start_str, to=end_str)
        .output(output_path, codec='copy')
        .overwrite_output()
        .run(quiet=True)
    )
    return output_path

def crop_vertical(input_path: str, output_path: str) -> str:
    """Crop horizontal video to 9:16 vertical (center crop) and scale to 1080x1920."""
    try:
        probe = ffmpeg.probe(input_path)
        video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        width = int(video_stream['width'])
        height = int(video_stream['height'])
    except Exception as e:
        print(f"Error probing video {input_path}: {e}")
        return output_path # fallback

    # Calculate crop dimensions for 9:16 aspect ratio based on height
    new_width = int(height * 9 / 16)
    x_offset = (width - new_width) // 2 
    
    (
        ffmpeg
        .input(input_path)
        .filter('crop', new_width, height, x_offset, 0)
        .filter('scale', 1080, 1920)
        .output(output_path, vcodec='libx264', crf=18, acodec='aac', preset='medium', movflags='faststart')
        .overwrite_output()
        .run(quiet=False) # Keep output for debugging if it fails
    )
    return output_path


def format_time(seconds: float) -> str:
    """Convert seconds to HH:MM:SS float format for FFmpeg."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hrs:02d}:{mins:02d}:{secs:06.3f}"


def generate_srt(segments: list[dict], output_path: str) -> str:
    """Generate SRT subtitle file from transcript segments."""
    def format_srt_time(seconds: float) -> str:
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, seg in enumerate(segments, 1):
            f.write(f"{i}\n")
            f.write(f"{format_srt_time(seg['start'])} --> {format_srt_time(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")
    
    return output_path


def process_clip(input_path: str, output_dir: Path, clip_idx: int, start_time: float, end_time: float, segments: list[dict] = None) -> dict:
    """"End to end function to create a ready-to-use 9:16 clip.
    Optional: pass matching segments to generate an SRT file side-by-side."""
    
    raw_clip_path = str(output_dir / f"raw_clip_{clip_idx:02d}.mp4")
    final_clip_path = str(output_dir / f"final_clip_{clip_idx:02d}.mp4")
    
    print(f"Clipping {start_time} to {end_time}...")
    clip_video(input_path, raw_clip_path, start_time, end_time)
    
    print(f"Cropping to 9:16 vertical...")
    crop_vertical(raw_clip_path, final_clip_path)
    
    srt_path = None
    if segments:
        srt_path = str(output_dir / "captions.srt")
        generate_srt(segments, srt_path)
        
    return {
        "final_video": final_clip_path,
        "raw_video": raw_clip_path,
        "srt": srt_path
    }
