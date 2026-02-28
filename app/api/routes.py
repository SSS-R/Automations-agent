import os
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from typing import List
from slowapi import Limiter
from slowapi.util import get_remote_address

from .schemas import VideoSessionOut, ClipOut, ProcessRequest, TaskStatusOut, StatsOut, FacelessGenerateRequest
from app.workers.tasks import process_video_task
from app.services.analytics import get_stats

router = APIRouter()
OUTPUT_DIR = Path("output")
limiter = Limiter(key_func=get_remote_address)

@router.post("/process", response_model=TaskStatusOut)
@limiter.limit("5/minute")
async def process_video(process_request: ProcessRequest, request: Request):
    """Submit a video URL to the Celery background worker."""
    task = process_video_task.delay(process_request.url)
    return TaskStatusOut(
        task_id=task.id,
        status="Job submitted to background worker",
        state=task.state,
        progress=0
    )

@router.post("/faceless/generate", response_model=TaskStatusOut)
@limiter.limit("5/minute")
async def generate_faceless_video(req: FacelessGenerateRequest, request: Request):
    """Submit a topic to generate a faceless video via background worker."""
    from app.workers.tasks import process_faceless_video_task
    task = process_faceless_video_task.delay(
        req.topic, 
        req.tone, 
        req.duration, 
        req.template, 
        req.font_preset, 
        req.color_palette,
        req.bgm_file
    )
    return TaskStatusOut(
        task_id=task.id,
        status="Faceless Job submitted to background worker",
        state=task.state,
        progress=0
    )

@router.post("/faceless/preview")
async def preview_faceless_video(req: FacelessGenerateRequest):
    """Return a mock script JSON configured with the requested template for UI preview."""
    # This skips the API and just returns a ready-to-render Remotion script struct
    return {
        "title": f"Preview: {req.topic}",
        "template": req.template,
        "font_preset": req.font_preset,
        "color_palette": req.color_palette,
        "bgm_file": req.bgm_file,
        "hook": "This is a preview hook!",
        "hookDurationInFrames": 90,
        "scenes": [
            {
                "text": "This is the first preview scene. It will show you how the template looks.",
                "durationInFrames": 120,
                "asset_file": "temp_vid_3536ffe3.mp4" # uses dummy asset
            }
        ],
        "cta": "Like and subscribe for more!",
        "ctaDurationInFrames": 90
    }

@router.get("/status/{task_id}", response_model=TaskStatusOut)
async def get_task_status(task_id: str):
    """Poll Celery for the task status."""
    task = process_video_task.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        return TaskStatusOut(task_id=task_id, state=task.state, status="Pending...", progress=0)
    elif task.state == 'PROGRESS':
        meta = task.info or {}
        return TaskStatusOut(
            task_id=task_id,
            state=task.state,
            status=meta.get('status', 'Processing...'),
            progress=meta.get('progress', 0)
        )
    elif task.state == 'SUCCESS':
        return TaskStatusOut(
            task_id=task_id,
            state=task.state,
            status="Complete",
            progress=100,
            result=task.result
        )
    else:
        # Failure or revoked
        return TaskStatusOut(
            task_id=task_id,
            state=task.state,
            status=str(task.info) if task.info else "Failed",
            progress=0
        )

@router.get("/videos", response_model=List[VideoSessionOut])
async def list_videos():
    """Scan the output directory and return all processed videos and their clips."""
    if not OUTPUT_DIR.exists():
        return []

    sessions = []
    
    # Iterate over video folders (e.g. "sample_sample")
    for video_folder in sorted(OUTPUT_DIR.iterdir(), key=os.path.getmtime, reverse=True):
        if not video_folder.is_dir():
            continue
            
        report_path = video_folder / "pipeline_report.json"
        if not report_path.exists():
            continue
            
        with open(report_path, "r", encoding="utf-8") as f:
            try:
                report_data = json.load(f)
            except json.JSONDecodeError:
                continue
                
        video_meta = report_data.get("original_video", {})
        video_title = video_meta.get("title", video_folder.name)
        video_id = video_meta.get("id", video_folder.name)
        
        clips = []
        for clip_data in report_data.get("clips", []):
            clip_idx = clip_data.get("clip_idx")
            clip_dir = video_folder / f"clip_{clip_idx:02d}"
            
            # Read caption.txt if exists
            caption_text = ""
            platform_captions = {"youtube": "", "tiktok": "", "instagram": ""}
            caption_path = clip_dir / "caption.txt"
            if caption_path.exists():
                with open(caption_path, "r", encoding="utf-8") as f:
                    caption_text = f.read()
                    
                # Basic parsing for platform specific texts
                parts = caption_text.split("\n\n")
                current_platform = None
                for part in parts:
                    if "[YouTube Shorts]" in part:
                        platform_captions["youtube"] = part.replace("[YouTube Shorts]", "").strip()
                    elif "[TikTok]" in part:
                        platform_captions["tiktok"] = part.replace("[TikTok]", "").strip()
                    elif "[Instagram Reels]" in part:
                        platform_captions["instagram"] = part.replace("[Instagram Reels]", "").strip()
            
            clips.append(ClipOut(
                id=f"clip_{clip_idx:02d}",
                clip_idx=clip_idx,
                video_url=f"/api/clips/{video_folder.name}/clip_{clip_idx:02d}",
                caption=caption_text,
                platform_captions=platform_captions,
                metadata=clip_data.get("metadata", {})
            ))
            
        sessions.append(VideoSessionOut(
            id=video_id,
            title=video_title,
            folder_name=video_folder.name,
            total_clips=len(clips),
            clips=clips
        ))

    return sessions

@router.get("/clips/{folder_name}/{clip_id}")
async def get_clip_video(folder_name: str, clip_id: str):
    """Serve the final MP4 video for a given clip."""
    video_path = OUTPUT_DIR / folder_name / clip_id / f"final_{clip_id}.mp4"
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video clip not found")
        
    return FileResponse(video_path, media_type="video/mp4")

@router.delete("/videos/{folder_name}")
async def delete_video_project(folder_name: str):
    """Delete a processed video project and all its clips."""
    import shutil
    
    project_path = OUTPUT_DIR / folder_name
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Video project not found")
    
    # Remove the output folder with all clips
    shutil.rmtree(project_path)
    
    # Also try to clean up the source video files if they exist
    # folder_name format is "Title_VideoID", extract video ID
    parts = folder_name.rsplit("_", 1)
    if len(parts) == 2:
        video_id = parts[1]
        videos_dir = Path("videos")
        temp_dir = Path("temp")
        for ext in [".mp4", ".webp", ".info.json", "_summary.json"]:
            vid_file = videos_dir / f"{video_id}{ext}"
            if vid_file.exists():
                vid_file.unlink()
        # Clean cached audio
        wav_file = temp_dir / f"{video_id}.wav"
        if wav_file.exists():
            wav_file.unlink()
        # Clean cached transcript
        cache_dir = temp_dir / "cache"
        transcript_file = cache_dir / f"{video_id}_transcript.json"
        if transcript_file.exists():
            transcript_file.unlink()
    
    return {"status": "deleted", "folder": folder_name}

@router.get("/stats", response_model=StatsOut)
async def get_pipeline_stats():
    """Return aggregate analytics stats for the dashboard."""
    return StatsOut(**get_stats())
