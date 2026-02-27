# Auto-Clipper ✂️🎬

Auto-Clipper is an AI-powered agentic application that automatically transforms long-form YouTube videos into viral, short-form clips optimized for TikTok, Instagram Reels, and YouTube Shorts. 

It handles everything from downloading the video to identifying the most engaging segments using Google Gemini, transcribing the audio, and rendering high-quality 9:16 vertical videos with animated, TikTok-style captions.

## ✨ Features

- **Automated Clipping**: Simply paste a YouTube URL, and the system does the rest.
- **AI-Powered Curation**: Uses Gemini 2.5 Flash to analyze transcripts and identify the most engaging "viral" moments.
- **High-Quality Video Processing**: Uses FFmpeg (CRF 18) to ensure near-lossless video quality.
- **Smart 9:16 Framing**: Employs a blurred-background dual-layer crop to ensure 100% of the original video content is visible in a vertical format without ugly black bars.
- **TikTok-Style Captions**: Integrates [Remotion](https://www.remotion.dev/) to programmatically render dynamic, word-by-word highlighted subtitles and animated "hook" text overlays.
- **Responsive Dashboard**: A sleek, minimal web interface to manage your parsed videos, view generated clips side-by-side, and easily copy links for sharing.
- **Asynchronous Processing**: Powered by Celery and Redis to handle heavy video processing tasks in the background without blocking the UI.

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python)
- **Task Queue**: Celery & Redis
- **AI Models**: Google GenAI SDK (`gemini-2.5-flash`), `faster-whisper` (local transcription)
- **Video Processing**: FFmpeg (Python `subprocess`), Remotion (React/TypeScript)
- **Downloader**: `yt-dlp`
- **Frontend**: Vanilla HTML / CSS / JS (Lucide Icons)

## 🚀 Getting Started

### Prerequisites

You need the following installed on your system:
- Python 3.10+
- Node.js & npm (for Remotion)
- FFmpeg (must be in your system's PATH)
- Redis Server (running locally on default port 6379)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/auto-clipper.git
   cd auto-clipper
   ```

2. **Set up the Python environment:**
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. **Set up Environment Variables:**
   Copy the example environment file and add your Gemini API key.
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

4. **Install Remotion Dependencies:**
   ```bash
   cd remotion-editor
   npm install
   cd ..
   ```

### Running the Application

To run the application locally, you need three separate terminal windows:

**Terminal 1: Start Redis**
Ensure your Redis server is running.
```bash
redis-server
```

**Terminal 2: Start the Celery Worker**
This processes the heavy background video tasks.
```bash
.\venv\Scripts\activate
celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```
*(Note: `--pool=solo` is recommended for Windows. On Linux/macOS, you can omit it).*

**Terminal 3: Start the FastAPI Server**
This hosts the backend API and the web frontend.
```bash
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### Usage

1. Open your browser and navigate to `http://127.0.0.1:8000`.
2. Paste a YouTube URL into the top bar and hit **Process**.
3. The video will be sent to the background worker. You can monitor the progress in the Celery terminal.
4. Once completed, your new viral clips will appear in the dashboard, complete with animated captions and blurred backgrounds!

## 🔒 Safety and Compliance

Auto-Clipper includes an API rate limiter to prevent spam requests and a UI compliance disclaimer to ensure end-users acknowledge copyright and licensing rights before processing content. Please ensure you have the appropriate rights to modify and distribute any downloaded material.

## 📜 License

MIT
