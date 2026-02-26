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
    
    # 1. Download or bypass if local file
    if os.path.exists(url):
        video_meta = {
            'id': Path(url).stem,
            'title': Path(url).stem,
            'filepath': url
        }
        print(f"✅ Using local file: {video_meta['title']}")
    else:
        video_meta = download_video(url)
        print(f"✅ Downloaded: {video_meta['title']}")
        
    video_id = video_meta['id']
    video_path = video_meta['filepath']
    
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
    video_out_dir = OUTPUT_DIR / f"{video_meta['title'].replace('/', '_').replace(':', '_')}_{video_id}"
    video_out_dir.mkdir(parents=True, exist_ok=True)
    
    # Save transcript and highlights
    with open(video_out_dir / "transcript.json", "w", encoding='utf-8') as f:
        json.dump(segments, f, indent=2)
    with open(video_out_dir / "highlights.json", "w", encoding='utf-8') as f:
        json.dump(highlights, f, indent=2)
    
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
            clip_dir = video_out_dir / f"clip_{idx:02d}"
            clip_dir.mkdir(exist_ok=True)
            
            # Generate FFmpeg outputs
            clip_paths = process_clip(
                input_path=video_path,
                output_dir=clip_dir,
                clip_idx=idx,
                start_time=start_sec,
                end_time=end_sec,
                segments=clip_segments
            )
            
            # Generate Caption
            clip_transcript_text = " ".join([s['text'] for s in clip_segments])
            caption = generate_caption(clip_transcript_text)
            
            # Write caption text
            with open(clip_dir / "caption.txt", "w", encoding='utf-8') as f:
                f.write(caption)
                
            # Write clip metadata
            with open(clip_dir / "metadata.json", "w", encoding='utf-8') as f:
                json.dump(clip, f, indent=2)
                
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
        
    # Generate summary report
    summary = f"""# Auto-Clipper Run Summary
## Video: {video_meta['title']}
- Original URL: {url}
- Total Highlights Detected: {len(highlights)}
- Total Clips Successfully Generated: {len(results)}

### Estimated Reach Potential
Assuming average performance metrics per clip across 3 main platforms (YouTube, TikTok, Instagram):
- Expected Views: {len(results) * 3000} - {len(results) * 15000} (1k-5k views per platform per clip)

All individual clips and captions have been saved in `{video_out_dir.absolute()}`.
"""
    with open(video_out_dir / "summary.md", "w", encoding='utf-8') as f:
        f.write(summary)
        
    print(f"\n🎉 Pipeline Complete! Outputs saved to: {video_out_dir}")
    return results
