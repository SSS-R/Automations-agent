import os
import json
from pathlib import Path
from typing import List, Dict

from .downloader import download_video
from .transcriber import full_transcribe_pipeline, format_for_llm
from .highlighter import detect_highlights, timestamp_to_seconds
from .clipper import process_clip
from .captioner import generate_caption

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

def orchestrate_pipeline(url: str):
    """
    End-to-end Python backend execution pipeline.
    1. Download (yt-dlp)
    2. Transcribe (faster-whisper)
    3. Highlight (Gemini Flash)
    4. Clip & Crop (ffmpeg-python)
    5. Caption Generation (Gemini Flash)
    """
    print(f"🚀 Starting Auto-Clipper Pipeline for: {url}")
    
    # 1. Download
    video_meta = download_video(url)
    video_id = video_meta['id']
    video_path = video_meta['filepath']
    print(f"✅ Downloaded: {video_meta['title']}")
    
    # 2. Transcribe
    segments = full_transcribe_pipeline(video_path, video_id)
    formatted_transcript = format_for_llm(segments)
    print(f"✅ Transcribed video. Length: {len(segments)} segments")
    
    # 3. Detect Highlights
    highlights = detect_highlights(formatted_transcript)
    if not highlights:
        print("❌ No highlights detected. Pipeline aborting.")
        return
        
    print(f"✅ Detected {len(highlights)} potential viral clips.")
    
    # Create output directory for this video
    video_out_dir = OUTPUT_DIR / f"{video_meta['title']}_{video_id}"
    video_out_dir.mkdir(parents=True, exist_ok=True)
    
    # 4 & 5. Process each clip and generate caption
    results = []
    for idx, clip in enumerate(highlights, 1):
        print(f"\n🎬 Processing Clip {idx}...")
        
        # Parse times
        start_sec = timestamp_to_seconds(clip['start'])
        end_sec = timestamp_to_seconds(clip['end'])
        
        # Get matching transcript segments for SRT
        # (Filter logic: segment end needs to be > clip start, segment start needs to be < clip end)
        clip_segments = [s for s in segments if s['end'] >= start_sec and s['start'] <= end_sec]
        
        try:
            # Generate FFmpeg outputs
            clip_paths = process_clip(
                video_id=video_id,
                input_path=video_path,
                clip_idx=idx,
                start_time=start_sec,
                end_time=end_sec,
                segments=clip_segments
            )
            
            # Generate Caption
            clip_transcript_text = " ".join([s['text'] for s in clip_segments])
            caption = generate_caption(clip_transcript_text)
            
            # Save all data together in output
            clip_dir = video_out_dir / f"clip_{idx:02d}"
            clip_dir.mkdir(exist_ok=True)
            
            # Write caption text
            with open(clip_dir / "caption.txt", "w", encoding='utf-8') as f:
                f.write(f"--- Meta ---\nHook: {clip.get('hook')}\nReason: {clip.get('reason')}\nViral Score: {clip.get('viral_score')}\n\n--- Caption ---\n{caption}")
                
            results.append({
                "clip_idx": idx,
                "paths": clip_paths,
                "metadata": clip,
                "caption": caption
            })
            print(f"✅ Clip {idx} finished.")
            
        except Exception as e:
            print(f"Error processing clip {idx}: {e}")
            
    # Save master run log
    with open(video_out_dir / "pipeline_report.json", "w", encoding='utf-8') as f:
        json.dump({
            "original_video": video_meta,
            "clips": results
        }, f, indent=2)
        
    print(f"\n🎉 Pipeline Complete! Outputs saved to: {video_out_dir}")
    return results
