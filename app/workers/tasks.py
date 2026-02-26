import json
import os
from pathlib import Path
from celery.utils.log import get_task_logger

from app.workers.celery_app import celery_app
from app.services.downloader import download_video
from app.services.transcriber import full_transcribe_pipeline, format_for_llm
from app.services.highlighter import detect_highlights, timestamp_to_seconds
from app.services.clipper import process_clip
from app.services.captioner import generate_caption

logger = get_task_logger(__name__)
OUTPUT_DIR = Path("output")

@celery_app.task(bind=True)
def process_video_task(self, url: str):
    """
    Background job equivalent of orchestrate_pipeline.
    Publishes state updates to be polled by the frontend.
    """
    logger.info(f"🚀 Starting Auto-Clipper Pipeline for: {url}")
    
    # 1. Download
    self.update_state(state='PROGRESS', meta={'status': 'Downloading video...', 'progress': 10})
    
    if os.path.exists(url):
        video_meta = {
            'id': Path(url).stem,
            'title': Path(url).stem,
            'filepath': url
        }
        logger.info(f"✅ Using local file: {video_meta['title']}")
    else:
        try:
            video_meta = download_video(url)
            logger.info(f"✅ Downloaded: {video_meta['title']}")
        except Exception as e:
            logger.error(f"Failed to download video: {e}")
            return {"error": f"Failed to download video: {str(e)}"}
        
    video_id = video_meta['id']
    video_path = video_meta['filepath']
    
    # 2. Transcribe
    self.update_state(state='PROGRESS', meta={'status': 'Transcribing audio...', 'progress': 30})
    try:
        segments = full_transcribe_pipeline(video_path, video_id)
        formatted_transcript = format_for_llm(segments)
        logger.info(f"✅ Transcribed video. Length: {len(segments)} segments")
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return {"error": f"Transcription failed: {str(e)}"}
    
    # 3. Detect Highlights
    self.update_state(state='PROGRESS', meta={'status': 'Detecting viral highlights...', 'progress': 50})
    try:
        highlights = detect_highlights(formatted_transcript)
        if not highlights:
            msg = "❌ No highlights detected. Pipeline aborting."
            logger.error(msg)
            return {"error": msg}
        logger.info(f"✅ Detected {len(highlights)} potential viral clips.")
    except Exception as e:
        logger.error(f"Highlight detection failed: {e}")
        return {"error": f"Highlight detection failed: {str(e)}"}
    
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
    total_clips = len(highlights)
    
    for idx, clip in enumerate(highlights, 1):
        progress_pct = 50 + int((idx / total_clips) * 45) # Progress 50 -> 95
        self.update_state(state='PROGRESS', meta={
            'status': f'Generating Clip {idx}/{total_clips}...', 
            'progress': progress_pct
        })
        logger.info(f"🎬 Processing Clip {idx}...")
        
        start_sec = timestamp_to_seconds(clip['start'])
        end_sec = timestamp_to_seconds(clip['end'])
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
            logger.info(f"✅ Clip {idx} finished.")
            
        except Exception as e:
            logger.error(f"Error processing clip {idx}: {e}")
            
    self.update_state(state='PROGRESS', meta={'status': 'Finalizing outputs...', 'progress': 99})
            
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
        
    logger.info(f"🎉 Pipeline Complete! Outputs saved to: {video_out_dir}")
    
    return {
        "status": "completed",
        "video_title": video_meta['title'],
        "output_dir": str(video_out_dir),
        "total_clips_generated": len(results)
    }
