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
from app.services.remotion_renderer import render_clip_with_remotion
from app.services.analytics import record_pipeline_start, record_pipeline_complete, record_pipeline_failed, record_clip

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
    
    # Record analytics
    run_id = record_pipeline_start(
        video_url=url,
        video_title=video_meta.get('title'),
        video_id=video_id
    )
    
    # Pre-calculate output directory so we can check cache
    video_out_dir = OUTPUT_DIR / f"{video_meta['title'].replace('/', '_').replace(':', '_')}_{video_id}"
    video_out_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Transcribe
    self.update_state(state='PROGRESS', meta={'status': 'Transcribing audio...', 'progress': 30})
    try:
        cached_transcript_path = video_out_dir / "transcript.json"
        
        if cached_transcript_path.exists():
            logger.info("♻️ Loading cached transcript...")
            with open(cached_transcript_path, "r", encoding='utf-8') as f:
                segments = json.load(f)
        else:
            segments = full_transcribe_pipeline(video_path, video_id)
            # Save new transcript
            with open(cached_transcript_path, "w", encoding='utf-8') as f:
                json.dump(segments, f, indent=2)
                
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
    
    def _process_single_clip(idx, clip):
        try:
            logger.info(f"🎬 Processing Clip {idx}...")
            start_sec = timestamp_to_seconds(clip['start'])
            end_sec = timestamp_to_seconds(clip['end'])
            clip_segments = [s for s in segments if s['end'] >= start_sec and s['start'] <= end_sec]
            
            clip_dir = video_out_dir / f"clip_{idx:02d}"
            clip_dir.mkdir(exist_ok=True)
            
            # Step 1: FFmpeg — clip + blurred background fit
            clip_paths = process_clip(
                input_path=video_path,
                output_dir=clip_dir,
                clip_idx=idx,
                start_time=start_sec,
                end_time=end_sec,
                segments=clip_segments
            )
            
            # Step 2: Remotion — animated captions + hook text overlay
            remotion_output = str(clip_dir / f"remotion_clip_{idx:02d}.mp4")
            hook_text = clip.get('hook', '')
            captions_json = clip_paths.get('captions_json')
            
            if captions_json and os.path.exists(captions_json):
                try:
                    duration = end_sec - start_sec
                    render_clip_with_remotion(
                        video_path=clip_paths['final_video'],
                        captions_json_path=captions_json,
                        hook_text=hook_text,
                        duration_seconds=duration,
                        output_path=remotion_output,
                    )
                    # Replace the FFmpeg-only clip with the Remotion version
                    if os.path.exists(remotion_output):
                        os.replace(remotion_output, clip_paths['final_video'])
                        logger.info(f"✅ Remotion render complete for Clip {idx}")
                except Exception as e:
                    logger.warning(f"⚠️ Remotion render failed for Clip {idx}, using FFmpeg-only version: {e}")
            
            # Step 3: Generate social media captions
            clip_transcript_text = " ".join([s['text'] for s in clip_segments])
            caption = generate_caption(clip_transcript_text)
            
            # Write caption text
            with open(clip_dir / "caption.txt", "w", encoding='utf-8') as f:
                f.write(caption)
                
            # Write clip metadata
            with open(clip_dir / "metadata.json", "w", encoding='utf-8') as f:
                json.dump(clip, f, indent=2)
                
            # Record clip analytics
            record_clip(
                run_id=run_id,
                clip_idx=idx,
                viral_score=clip.get('viral_score'),
                start_time=clip.get('start'),
                end_time=clip.get('end'),
                hook=clip.get('hook')
            )
            
            logger.info(f"✅ Clip {idx} finished.")
            return {
                "clip_idx": idx,
                "paths": clip_paths,
                "metadata": clip,
                "caption": caption
            }
        except Exception as e:
            logger.error(f"Error processing clip {idx}: {e}")
            return None

    import concurrent.futures
    
    # Process clips concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_idx = {
            executor.submit(_process_single_clip, idx, clip): idx 
            for idx, clip in enumerate(highlights, 1)
        }
        
        completed = 0
        for future in concurrent.futures.as_completed(future_to_idx):
            res = future.result()
            if res:
                results.append(res)
            
            completed += 1
            progress_pct = 50 + int((completed / total_clips) * 45) # Progress 50 -> 95
            self.update_state(state='PROGRESS', meta={
                'status': f'Generated Clip {completed}/{total_clips}...', 
                'progress': progress_pct
            })
            
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
        
    # Record analytics completion
    record_pipeline_complete(run_id, clips_generated=len(results))
    
    logger.info(f"🎉 Pipeline Complete! Outputs saved to: {video_out_dir}")
    
    return {
        "status": "completed",
        "video_title": video_meta['title'],
        "output_dir": str(video_out_dir),
        "total_clips_generated": len(results)
    }
