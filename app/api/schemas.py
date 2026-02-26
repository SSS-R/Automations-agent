from pydantic import BaseModel
from typing import List, Optional

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
