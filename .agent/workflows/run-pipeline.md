---
description: How to run the full AI clipping pipeline from video URL to final clips
---

# AI Clipping Pipeline Workflow

## Prerequisites
- Python 3.11+ installed
- FFmpeg installed and in PATH
- `.env` file configured with `OPENAI_API_KEY` (or `GOOGLE_API_KEY` for Gemini)
- Virtual environment activated

## Steps

// turbo-all

1. **Activate virtual environment**
```powershell
cd "c:\Automations agent"
.\venv\Scripts\Activate.ps1
```

2. **Start the FastAPI server**
```powershell
cd "c:\Automations agent"
python -m uvicorn app.main:app --reload --port 8000
```

3. **Process a video (via API)**
```powershell
# Single video URL
Invoke-RestMethod -Uri "http://localhost:8000/api/process" -Method POST -ContentType "application/json" -Body '{"url": "https://youtube.com/watch?v=VIDEO_ID"}'
```

4. **Process a video (via CLI)**
```powershell
cd "c:\Automations agent"
python -m app.services.pipeline --url "https://youtube.com/watch?v=VIDEO_ID"
```

5. **Check output**
- Clips will be saved in `./clips/[video-title]-[date]/`
- Each clip folder contains: `clip.mp4`, `caption.txt`, `metadata.json`

## Manual Upload Workflow
1. Open the output folder
2. For each clip:
   - Upload `.mp4` to YouTube Shorts / Instagram Reels / TikTok
   - Copy-paste content from `caption.txt` as the description
   - Add any additional tags as needed
