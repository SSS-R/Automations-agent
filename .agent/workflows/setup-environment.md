---
description: How to set up the development environment for the AI clipping agent
---

# Environment Setup Workflow

## Steps

// turbo-all

1. **Create and activate virtual environment**
```powershell
cd "c:\Automations agent"
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. **Install Python dependencies**
```powershell
cd "c:\Automations agent"
pip install fastapi uvicorn openai python-dotenv yt-dlp pydantic faster-whisper google-generativeai
```

3. **Verify FFmpeg is installed**
```powershell
ffmpeg -version
```
If not installed, install via:
```powershell
winget install Gyan.FFmpeg
```

4. **Create `.env` file**
Create `c:\Automations agent\.env` with:
```
OPENAI_API_KEY=sk-your-key-here
GOOGLE_API_KEY=your-gemini-key-here
```

5. **Create required directories**
```powershell
cd "c:\Automations agent"
mkdir -Force videos, clips, subtitles, temp, app, app\api, app\services, app\workers, app\utils, app\models, tests
```

6. **Verify setup**
```powershell
cd "c:\Automations agent"
python -c "import fastapi; import openai; import yt_dlp; print('All dependencies installed successfully!')"
```
