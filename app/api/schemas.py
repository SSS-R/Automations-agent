from pydantic import BaseModel
from typing import List, Optional, Any

class ProcessRequest(BaseModel):
    url: str

class TaskStatusOut(BaseModel):
    task_id: str
    status: str
    state: str
    progress: int
    result: Optional[Any] = None

class ClipOut(BaseModel):
    id: str
    clip_idx: int
    video_url: str
    caption: str
    platform_captions: dict # e.g. {"youtube": "...", "tiktok": "..."}
    metadata: dict

class VideoSessionOut(BaseModel):
    id: str
    title: str
    folder_name: str
    total_clips: int
    clips: List[ClipOut]
