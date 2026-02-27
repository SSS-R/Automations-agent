"""
Render all existing clips through Remotion using already-generated data.
NO API calls — uses existing captions JSON, metadata, and FFmpeg clips.
"""
import json
import os
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

from app.services.remotion_renderer import render_clip_with_remotion
from app.services.highlighter import timestamp_to_seconds

OUTPUT_DIR = Path("output")


def render_existing_clips(video_folder: str = None):
    """Render all clips in the output directory (or a specific folder)."""
    
    if video_folder:
        folders = [OUTPUT_DIR / video_folder]
    else:
        folders = [f for f in OUTPUT_DIR.iterdir() if f.is_dir()]
    
    total_rendered = 0
    total_failed = 0
    
    for folder in folders:
        report_path = folder / "pipeline_report.json"
        if not report_path.exists():
            print(f"⏭️ Skipping {folder.name} — no pipeline_report.json")
            continue
        
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        
        print(f"\n📁 Processing: {folder.name}")
        print(f"   Clips found: {len(report.get('clips', []))}")
        
        for clip_data in report.get("clips", []):
            idx = clip_data["clip_idx"]
            clip_dir = folder / f"clip_{idx:02d}"
            
            final_video = clip_dir / f"final_clip_{idx:02d}.mp4"
            captions_json = clip_dir / f"captions_{idx:02d}.json"
            metadata_path = clip_dir / "metadata.json"
            
            if not final_video.exists():
                print(f"   ⏭️ Clip {idx}: no video file, skipping")
                continue
            
            if not captions_json.exists():
                print(f"   ⏭️ Clip {idx}: no captions JSON, skipping")
                continue
            
            # Read metadata for hook text and timestamps
            hook_text = ""
            duration = 30  # default
            if metadata_path.exists():
                with open(metadata_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    hook_text = meta.get("hook", "")
                    start = timestamp_to_seconds(meta.get("start", "0"))
                    end = timestamp_to_seconds(meta.get("end", "30"))
                    duration = end - start
            
            remotion_output = str(clip_dir / f"remotion_clip_{idx:02d}.mp4")
            
            print(f"   🎬 Clip {idx}: Rendering with Remotion ({duration:.0f}s, hook: \"{hook_text[:40]}...\")")
            
            try:
                render_clip_with_remotion(
                    video_path=str(final_video),
                    captions_json_path=str(captions_json),
                    hook_text=hook_text,
                    duration_seconds=duration,
                    output_path=remotion_output,
                )
                
                # Replace the FFmpeg-only clip with the Remotion version
                if os.path.exists(remotion_output):
                    os.replace(remotion_output, str(final_video))
                    print(f"   ✅ Clip {idx}: Remotion render complete!")
                    total_rendered += 1
                else:
                    print(f"   ❌ Clip {idx}: Remotion output not found")
                    total_failed += 1
                    
            except Exception as e:
                print(f"   ❌ Clip {idx}: Render failed — {e}")
                total_failed += 1
    
    print(f"\n🎉 Done! Rendered: {total_rendered}, Failed: {total_failed}")


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else None
    render_existing_clips(folder)
