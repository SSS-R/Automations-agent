import subprocess
import json
import os
from pathlib import Path

REMOTION_DIR = Path(__file__).resolve().parent.parent.parent / "remotion-editor"

def create_caption_pages(captions_json_path: str, combine_ms: int = 800) -> list:
    """Convert word-level captions JSON into page groups for display.
    
    Groups words that appear within `combine_ms` of each other into pages,
    similar to @remotion/captions createTikTokStyleCaptions.
    """
    with open(captions_json_path, 'r', encoding='utf-8') as f:
        captions = json.load(f)
    
    if not captions:
        return []
    
    pages = []
    current_page_tokens = [captions[0]]
    
    for i in range(1, len(captions)):
        token = captions[i]
        prev_token = current_page_tokens[-1]
        
        # If this word is close enough to the previous, add to same page
        if token['startMs'] - prev_token['endMs'] < combine_ms and len(current_page_tokens) < 8:
            current_page_tokens.append(token)
        else:
            # Finalize current page
            pages.append({
                "startMs": current_page_tokens[0]['startMs'],
                "endMs": current_page_tokens[-1]['endMs'],
                "tokens": [{"text": t['text'], "fromMs": t['startMs']} for t in current_page_tokens]
            })
            current_page_tokens = [token]
    
    # Don't forget the last page
    if current_page_tokens:
        pages.append({
            "startMs": current_page_tokens[0]['startMs'],
            "endMs": current_page_tokens[-1]['endMs'],
            "tokens": [{"text": t['text'], "fromMs": t['startMs']} for t in current_page_tokens]
        })
    
    return pages


def get_video_duration_frames(duration_seconds: float, fps: int = 30) -> int:
    """Convert duration in seconds to frame count."""
    return int(duration_seconds * fps)


def render_clip_with_remotion(
    video_path: str,
    captions_json_path: str,
    hook_text: str,
    duration_seconds: float,
    output_path: str,
    fps: int = 30
) -> str:
    """Render a clip using Remotion with animated captions.
    
    Args:
        video_path: Absolute path to the FFmpeg-processed clip (with blurred bg)
        captions_json_path: Path to captions JSON file
        hook_text: Text to display in the first 3 seconds
        duration_seconds: Clip duration in seconds
        output_path: Where to save the final rendered video
        fps: Frames per second (default 30)
    
    Returns:
        Path to the rendered video
    """
    # Convert captions to page format
    caption_pages = create_caption_pages(captions_json_path)
    
    # Build props for Remotion
    duration_frames = get_video_duration_frames(duration_seconds, fps)
    
    # Video path needs to be a file:// URI for Remotion to access local files
    video_abs = os.path.abspath(video_path).replace('\\', '/')
    video_uri = f"file:///{video_abs}"
    
    props = {
        "videoSrc": video_uri,
        "captionPages": caption_pages,
        "hookText": hook_text,
        "durationInFrames": duration_frames,
    }
    
    # Write props to a temp file (too large for CLI args)
    # Use a path WITHOUT spaces to avoid Windows shell quoting issues
    import tempfile
    props_fd, props_path = tempfile.mkstemp(suffix='.json', prefix='remotion_props_')
    os.close(props_fd)
    with open(props_path, 'w', encoding='utf-8') as f:
        json.dump(props, f)
    
    output_abs = os.path.abspath(output_path)
    
    # Run Remotion render
    # On Windows, npx is a cmd script so we need shell=True
    # Use subprocess.list2cmdline to properly escape paths with spaces
    cmd_parts = [
        'npx', 'remotion', 'render',
        'src/index.ts', 'ShortClip',
        f'"{output_abs}"',
        f'--props="{props_path}"',
        '--codec=h264',
        '--crf=18',
        '--pixel-format=yuv420p',
        f'--frames=0-{duration_frames - 1}',
    ]
    cmd_str = ' '.join(cmd_parts)
    
    print(f"🎬 Rendering with Remotion ({duration_frames} frames)...")
    
    result = subprocess.run(
        cmd_str,
        capture_output=True,
        text=True,
        cwd=str(REMOTION_DIR),
        timeout=300,  # 5 minute timeout
        shell=True,   # Required on Windows for npx
    )
    
    if result.returncode != 0:
        print(f"❌ Remotion render failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        raise Exception(f"Remotion render failed: {result.stderr[:500]}")
    
    print(f"✅ Remotion render complete: {output_abs}")
    
    # Cleanup props file
    try:
        os.remove(props_path)
    except:
        pass
    
    return output_path
