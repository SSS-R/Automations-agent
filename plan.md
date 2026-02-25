# 📁 AI Automated Clipping & Multi-Platform Posting Agent

## 🧠 Project Vision

An AI-powered agent that automatically turns long-form videos into viral short clips and distributes them across multiple social platforms — **hands-free**.

---

## 🔥 The Problem

Creators waste **5–10 hours/week** manually:
- Finding highlight moments
- Cutting vertical clips
- Adding subtitles
- Writing captions
- Uploading to multiple platforms

Short-form content drives the most growth on **YouTube Shorts, Instagram Reels, Facebook Reels, and TikTok**. Consistency wins — but consistency is exhausting.

---

## 💡 The Solution

A fully automated AI clipping and publishing agent that:

1. Accepts a video link or file
2. Transcribes and analyzes content
3. Detects the most engaging moments
4. Cuts vertical short clips
5. Adds subtitles automatically
6. Generates captions + hashtags
7. Schedules or uploads across platforms

**All in one pipeline.**

---

## 🏗️ System Architecture

```
User Input (URL / File Upload)
        ↓
Video Downloader (yt-dlp)
        ↓
Audio Extraction (FFmpeg)
        ↓
Transcription (Whisper.cpp via @remotion/install-whisper-cpp — FREE)
        ↓
LLM Highlight Detection (GPT-4o-mini)
        ↓
Clip Timestamp Generator
        ↓
FFmpeg Clipping Engine (vertical 9:16 crop)
        ↓
🎬 Remotion Rendering Engine
  ├─ TikTok-style animated captions (@remotion/captions)
  ├─ Custom overlays, hooks, text animations
  ├─ Branded intro/outro templates
  └─ Final MP4 render (React → video)
        ↓
Caption & Hashtag Generator (GPT-4o-mini)
        ↓
Output Folder / Manual Upload
```

---

## 🛠️ Tech Stack (Beta — VPS Deployed)

| Layer              | Technology                          | Cost       |
|--------------------|-------------------------------------|------------|
| **Language**       | Python 3.11+ & Node.js 18+         | Free       |
| **API Framework**  | FastAPI + Uvicorn                   | Free       |
| **Transcription**  | `faster-whisper` (local on VPS)     | Free       |
| **AI / LLM**       | GPT-4o-mini (or Gemini Flash free)  | $0–$5/mo   |
| **Video Editing**  | **Remotion** (React → video)        | Free (personal) |
| **Captions**       | `@remotion/captions` (TikTok-style) | Free       |
| **Media**          | FFmpeg (CLI) + `ffmpeg-python`      | Free       |
| **Download**       | yt-dlp (Python API)                 | Free       |
| **Task Queue**     | Celery + Redis                      | Free       |
| **Storage**        | VPS disk (local)                    | Free       |
| **Hosting**        | **VPS (Hetzner CX22 / Oracle Free)**| **$0–$5/mo** |

> 💡 **Everything runs on a $5 VPS** (or Oracle Cloud free tier). No need to keep your PC on 24/7. The VPS runs unattended, processing videos in the background.

### Recommended VPS Options

| Provider | Plan | RAM | Storage | Price | Notes |
|----------|------|-----|---------|-------|-------|
| **Oracle Cloud** | ARM Ampere | 24 GB | 200 GB | **FREE forever** | Best value, ARM CPU |
| **Hetzner** | CX22 | 4 GB | 40 GB | €4.15/mo (~$5) | Reliable, EU-based |
| **Hostinger** | KVM 2 | 8 GB | 100 GB | $6.99/mo | Good for starters |
| **Contabo** | VPS S | 8 GB | 200 GB | €5.99/mo | Most storage |

> ⚠️ **Oracle Cloud free tier** gives you 24GB RAM — that's enough to run the `medium` Whisper model for best transcription quality. On a $5 VPS (4GB RAM), use the `small` model.

---

## 🚀 PHASE 1 — MVP CORE ENGINE (Beta / Personal Use)

**Goal:** Input a video → Get 3–5 vertical short clips with subtitles & captions. Manually upload to platforms. Start earning $2–$10/day.

---

### Phase 1.1 — Environment Setup

- [ ] Create project directory structure
- [ ] Setup Python virtual environment (`venv`)
- [ ] Install core dependencies:
  ```
  fastapi uvicorn openai python-dotenv yt-dlp celery redis pydantic
  ```
- [ ] Verify FFmpeg is installed and in PATH
- [ ] Create `.env` file for API keys (`OPENAI_API_KEY`)
- [ ] Create FastAPI entry point (`app/main.py`)

**Deliverable:** Working FastAPI server at `http://localhost:8000`

---

### Phase 1.2 — Video Ingestion

#### 1.2.1 — Link Detection
- [ ] Auto-detect YouTube / Twitter / Facebook / Instagram / TikTok URLs
- [ ] Validate URLs before processing

#### 1.2.2 — Video Download
- [ ] Download video via `yt-dlp` with best quality
- [ ] Save metadata (title, duration, channel) to JSON
- [ ] Support direct file upload as alternative input

**Command:**
```bash
yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]" -o "videos/%(title)s.%(ext)s" <URL>
```

**Deliverable:** Video + metadata JSON saved locally.

---

### Phase 1.3 — Smart Transcription (3-Tier Strategy)

> 💡 **Key insight:** Many platforms already provide transcripts for free. We should always try to grab those FIRST before wasting VPS CPU on local transcription.

#### Tier 1 — Fetch Existing Subtitles (FREE + INSTANT)
- [ ] Use `yt-dlp --write-auto-sub --sub-lang en --skip-download` to grab YouTube auto-captions
- [ ] Parse `.vtt` / `.srt` files into our timestamped format
- [ ] Works on YouTube, TikTok (often), and many other platforms
- [ ] **Cost: $0 | Speed: instant**

```python
# yt-dlp can download subtitles without downloading the video
def fetch_existing_transcript(url: str) -> list[dict] | None:
    """Try to get existing subtitles from the platform."""
    ydl_opts = {
        'writeautomaticsub': True,
        'writesubtitles': True,
        'subtitleslangs': ['en'],
        'skip_download': True,
        'outtmpl': 'temp/%(title)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # Parse the downloaded .vtt/.srt file
        # Return structured segments or None if no subs found
```

#### Tier 2 — Local Transcription with `faster-whisper` (FREE on VPS)
- [ ] Only runs if Tier 1 finds no subtitles
- [ ] Extract audio: `ffmpeg -i input.mp4 -ar 16000 -ac 1 audio.wav`
- [ ] Transcribe using `faster-whisper` with `small` model (4GB RAM VPS)
- [ ] Word-level timestamps for animated captions
- [ ] Cache results to avoid re-processing
- [ ] **Cost: $0 | Speed: ~5 min for 30-min video**

#### Tier 3 — Whisper API (Paid fallback — rarely needed)
- [ ] Only if Tier 1 + Tier 2 both fail (e.g., non-English, corrupt audio)
- [ ] Send to OpenAI Whisper API
- [ ] **Cost: $0.006/min | Speed: ~30 seconds**

#### Transcription Flow
```
Input URL
  ↓
Try yt-dlp subtitle download (FREE, instant)
  ↓ Found? → Use it ✅
  ↓ Not found?
Extract audio with FFmpeg
  ↓
Run faster-whisper locally (FREE, ~5 min)
  ↓ Success? → Use it ✅
  ↓ Failed?
Send to Whisper API ($0.006/min)
  ↓ → Use it ✅
```

**Output Format (same for all tiers):**
```json
[
  { "start": 0.0, "end": 5.2, "text": "Welcome back everyone..." },
  { "start": 5.2, "end": 12.1, "text": "Today we're going to talk about..." }
]
```

> 🔥 **In practice, 80%+ of YouTube videos have auto-captions.** You'll rarely need Tier 2 or 3.

**Deliverable:** Structured transcript with timestamps — obtained for $0 most of the time.

---

### Phase 1.4 — Highlight Detection (LLM)

#### Prompt Template
```
You are a viral short-form content editor.

Analyze this transcript with timestamps. Select the 3-5 most engaging 
segments (20-60 seconds each) that would make viral short-form clips.

Prioritize:
- Strong hooks (first 3 seconds must grab attention)
- Emotional peaks
- Surprising statements
- Actionable advice
- Controversial or bold opinions

Return JSON array:
[
  {
    "start": "00:02:10",
    "end": "00:02:45",
    "hook": "suggested opening hook text",
    "reason": "strong emotional statement with surprise element",
    "viral_score": 8
  }
]
```

- [ ] Send transcript to GPT-4o-mini
- [ ] Parse JSON response
- [ ] Sort by `viral_score` descending
- [ ] Allow manual override / selection

**Cost:** ~$0.01–0.03 per video (GPT-4o-mini is extremely cheap).

**Deliverable:** JSON list of clip timestamps with hooks.

---

### Phase 1.5 — Clipping Engine

- [ ] Extract clips using FFmpeg with precise timestamps
- [ ] Apply vertical crop (9:16 aspect ratio)
- [ ] Re-encode for platform compatibility

**Commands:**
```bash
# Extract clip
ffmpeg -i input.mp4 -ss 00:02:10 -to 00:02:45 -c copy clip_raw.mp4

# Vertical crop (center crop to 9:16)
ffmpeg -i clip_raw.mp4 -vf "crop=ih*9/16:ih" -c:a copy clip_vertical.mp4
```

**Deliverable:** Vertical 9:16 short clips ready for subtitles.

---

### Phase 1.6 — Remotion Video Editing & Rendering Engine

> **This is the game-changer.** Remotion lets you create professional-quality videos programmatically using React. Instead of basic FFmpeg subtitle burn-in, you get animated captions, custom overlays, branded templates — all rendered to MP4.

#### 1.6.1 — Remotion Project Setup
- [ ] Initialize Remotion project (`npx create-video@latest`)
- [ ] Install Remotion packages:
  ```bash
  npm i --save-exact remotion @remotion/cli @remotion/captions @remotion/install-whisper-cpp
  ```
- [ ] Configure Remotion for 9:16 vertical output (1080×1920)

#### 1.6.2 — Local Transcription with Whisper.cpp (FREE)
- [ ] Use `@remotion/install-whisper-cpp` to install Whisper locally
- [ ] Transcribe audio with token-level timestamps
- [ ] Convert output to `Caption[]` format using `toCaptions()`

```typescript
import { installWhisperCpp, downloadWhisperModel, transcribe, toCaptions } from '@remotion/install-whisper-cpp';

// One-time setup
await installWhisperCpp({ to: './whisper.cpp', version: '1.5.5' });
await downloadWhisperModel({ model: 'medium.en', folder: './whisper.cpp' });

// Transcribe
const output = await transcribe({
  model: 'medium.en',
  whisperPath: './whisper.cpp',
  whisperCppVersion: '1.5.5',
  inputPath: '/path/to/audio.wav',
  tokenLevelTimestamps: true,
});

const { captions } = toCaptions({ whisperCppOutput: output });
```

> 💰 **Cost: $0.** No API fees — runs entirely on your machine.

#### 1.6.3 — TikTok-Style Animated Captions
- [ ] Use `@remotion/captions` with `createTikTokStyleCaptions()`
- [ ] Word-by-word highlight animation (the viral subtitle style)
- [ ] Customizable fonts, colors, and animation timing
- [ ] Support multiple caption styles (karaoke, pop-in, fade)

#### 1.6.4 — Custom Video Templates (React Components)
- [ ] **Hook overlay** — Animated text for the first 3 seconds
- [ ] **Progress bar** — Retention-boosting progress indicator
- [ ] **Branded intro/outro** — 1-2 second branded bumper
- [ ] **Lower third** — Channel name / CTA overlay
- [ ] **Background effects** — Gradient, blur, particle overlays

#### 1.6.5 — Render Pipeline
- [ ] Render final clips to MP4 via Remotion CLI or `renderMedia()`
- [ ] Configure encoding (H.264, CRF 18, high quality)
- [ ] Batch render multiple clips

```bash
# Render a single clip
npx remotion render src/index.ts ShortClip out/clip_01.mp4 --props='{"clipData": "clip_01.json"}'
```

**Deliverable:** Professional-quality subtitled vertical clips with animated captions and overlays.

---

### Phase 1.6-ALT — FFmpeg Fallback (Simple Mode)

For quick/simple clips without Remotion rendering:

```bash
# Basic subtitle burn-in
ffmpeg -i clip.mp4 -vf "subtitles=clip.srt:force_style='FontName=Arial Bold,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Alignment=10'" output.mp4
```

- [ ] FFmpeg fallback for when Remotion isn't needed
- [ ] Useful for batch processing speed

**Deliverable:** Basic subtitled clips (quick mode).

---

### Phase 1.7 — Caption & Hashtag Generator

#### Prompt:
```
Generate a viral caption for this short video clip.

Rules:
- Under 150 characters
- Include a hook or question
- Conversational tone
- Add 5 relevant trending hashtags
- Include 1 broad hashtag and 4 niche hashtags

Clip context: [clip transcript]
```

- [ ] Generate caption per clip
- [ ] Save as `caption.txt` alongside each clip
- [ ] Include platform-specific variations (YouTube vs TikTok vs Instagram)

**Deliverable:** `caption.txt` files per clip.

---

### Phase 1.8 — Output Organization

```
/output
  /[video-title]-[date]
    /clip_01
      clip_01.mp4          # Final subtitled vertical clip
      caption.txt          # Caption + hashtags
      metadata.json        # Timestamps, viral score, etc.
    /clip_02
      ...
    /clip_03
      ...
    transcript.json        # Full transcript
    highlights.json        # All detected highlights
```

- [ ] Organize output into clean folder structure
- [ ] Generate summary report (total clips, estimated reach)

---

## 📲 PHASE 2 — POSTING SYSTEM

### Phase 2.1 — Manual Posting (Safe Mode — START HERE)

- [ ] Output clips to organized folders
- [ ] Copy-paste captions from `caption.txt`
- [ ] Manually upload to platforms

> **Why manual first?** Avoid API bans, learn what works, test content quality before automating.

### Phase 2.2 — Semi-Automated Posting

- [ ] Build simple web dashboard to preview clips
- [ ] One-click copy caption
- [ ] Open platform upload page in browser

### Phase 2.3 — Full API Integration (Future)

| Platform   | API                    | Requirements         |
|------------|------------------------|----------------------|
| YouTube    | YouTube Data API v3    | OAuth, quota limits  |
| Instagram  | Graph API              | Business account     |
| Facebook   | Graph API              | Page + verification  |
| TikTok     | TikTok API v2          | Developer account    |
| X/Twitter  | X API (Paid tier)      | $100/mo basic        |

- [ ] YouTube upload via API (first target)
- [ ] Facebook/Instagram Graph API
- [ ] TikTok API integration
- [ ] OAuth token storage (encrypted)

---

## 🔁 PHASE 3 — BACKGROUND JOB QUEUE

### Phase 3.1 — Celery + Redis Setup

- [ ] Install and configure Redis (local or Docker)
- [ ] Define Celery tasks:
  - `download_video` → `transcribe` → `detect_highlights` → `clip_video` → `generate_subtitles` → `generate_caption`
- [ ] Chain tasks into pipeline
- [ ] Add progress tracking

### Phase 3.2 — Batch Processing

- [ ] Accept multiple video URLs
- [ ] Process queue in background
- [ ] Notification on completion (email / webhook)

**Deliverable:** Non-blocking async pipeline.

---

## 📊 PHASE 4 — OPTIMIZATION

### 4.1 — Cost Optimization

- [ ] Cache transcripts (avoid re-transcription)
- [ ] Limit GPT context window (send only relevant transcript)
- [ ] Use GPT-4o-mini exclusively (not GPT-4o)
- [ ] Batch API calls where possible
- [ ] Consider local Whisper (whisper.cpp) for zero transcription cost

### 4.2 — Performance Optimization

- [ ] Multi-worker Celery processing
- [ ] Compress final clips (H.264, CRF 23)
- [ ] Auto-clean temp files after processing
- [ ] Parallel clip generation

### 4.3 — Quality Optimization

- [ ] A/B test different hook styles
- [ ] Track which clips get most views (manual log initially)
- [ ] Refine LLM prompts based on performance data

---

## 🔐 PHASE 5 — SAFETY & COMPLIANCE

- [ ] Only process user-owned or licensed content
- [ ] No headless browser automation for uploads (use official APIs)
- [ ] Respect platform API rate limits
- [ ] Add rate limiting to API endpoints
- [ ] Store OAuth tokens encrypted (Fernet / environment variables)
- [ ] Add content moderation check before posting

---

## 💰 COST ESTIMATION (Personal/Beta Scale)

| Component         | Monthly Cost   | Notes                         |
|-------------------|----------------|-------------------------------|
| **VPS**           | $0–$5          | Oracle free tier or Hetzner CX22 |
| **Transcription** | $0             | `faster-whisper` runs on VPS  |
| **LLM (GPT-4o-mini)** | $1–$5     | Highlight detection + captions |
| **Remotion**      | $0             | Free for personal use         |
| **Redis**         | $0             | Runs on VPS                   |
| **Domain (optional)** | $0–$1     | Free subdomain or ~$1/mo      |
| **Total**         | **$1–$10/mo**  |                               |

> 🔥 With Oracle free tier + Gemini Flash free tier = **$0/month total!**

### Revenue Target

| Metric              | Conservative | Moderate  | Optimistic |
|----------------------|-------------|-----------|------------|
| Shorts/day           | 5           | 10        | 20         |
| Monthly views        | 50K         | 200K      | 500K+      |
| Revenue/month        | $30–60      | $100–300  | $300–1000  |
| **Net profit/month** | **$25–55**  | **$90–295** | **$290–995** |

> Break-even at just **~1,000 views/day** across all platforms.

---

## 📈 PHASE 6 — SCALING TO SAAS (Future)

### 6.1 — User Accounts
- [ ] JWT authentication
- [ ] User dashboard
- [ ] Usage tracking & analytics

### 6.2 — Subscription System
- [ ] Stripe integration
- [ ] Tiered plans:
  - **Starter** — $15/mo (10 videos/mo, 3 clips each)
  - **Pro** — $39/mo (30 videos/mo, 5 clips each)
  - **Agency** — $79/mo (unlimited, priority queue)
- [ ] Usage quotas & overage billing

### 6.3 — Multi-Tenant Architecture
- [ ] Per-user storage (S3-compatible)
- [ ] Isolated job queues
- [ ] Admin dashboard

---

## 📁 DIRECTORY STRUCTURE

```
/automations-agent
  /app                        # Python backend
    main.py                 # FastAPI entry point
    config.py               # Settings & env loading
    /api
      routes.py             # API endpoints
      schemas.py            # Request/Response models
    /services
      downloader.py         # yt-dlp video download
      highlighter.py        # LLM highlight detection
      clipper.py            # FFmpeg clipping engine
      captioner.py          # Caption & hashtag generation
      pipeline.py           # Orchestrate full pipeline
    /workers
      tasks.py              # Celery task definitions
      celery_app.py         # Celery configuration
    /utils
      ffmpeg_utils.py       # FFmpeg command helpers
      time_utils.py         # Timestamp parsing/formatting
      file_utils.py         # File management helpers
    /models
      video.py              # Video metadata model
      clip.py               # Clip data model
  /remotion-editor            # Remotion (Node.js) video editor
    /src
      index.ts              # Entry point
      Root.tsx              # Composition registry
      /components
        ShortClip.tsx       # Main short clip template
        AnimatedCaptions.tsx # TikTok-style captions
        HookOverlay.tsx     # Hook text animation
        ProgressBar.tsx     # Retention progress bar
        LowerThird.tsx      # Channel/CTA overlay
      /templates
        motivational.tsx    # Motivational niche template
        tech-news.tsx       # Tech/AI news template
        podcast.tsx         # Podcast clip template
    /public                 # Static assets (clips to render)
    package.json
    tsconfig.json
  /scripts
    transcribe.ts           # Whisper.cpp transcription script
    render_clips.ts         # Batch render script
  /videos                   # Downloaded source videos
  /clips                    # Generated clips output
  /subtitles                # SRT files
  /temp                     # Temporary processing files
  /tests
    test_highlighter.py
    test_clipper.py
    test_pipeline.py
  .env                      # API keys (gitignored)
  .gitignore
  requirements.txt          # Python deps
  README.md
```

---

## 🧪 TESTING STRATEGY

### Unit Tests
- [ ] Transcript parsing & formatting
- [ ] Timestamp conversion (HH:MM:SS ↔ seconds)
- [ ] FFmpeg command generation
- [ ] Caption output validation

### Integration Tests
- [ ] Full pipeline test with a short sample video
- [ ] End-to-end: URL → clips + captions

### Manual Tests
- [ ] Upload generated clips to each platform
- [ ] Verify subtitle readability on mobile
- [ ] Check video quality (resolution, audio sync)

---

## 🎯 VERSION ROADMAP

| Version | Features                                    | Target      |
|---------|---------------------------------------------|-------------|
| v0.1    | Single video → 1 clip with subtitles        | Week 1      |
| v0.2    | Multiple clips + captions + hashtags        | Week 2      |
| v0.3    | Background queue + batch processing         | Week 3      |
| v0.4    | YouTube auto-upload (API)                   | Week 4      |
| v0.5    | Web dashboard for preview                   | Week 5-6    |
| v1.0    | Multi-platform + polished UI                | Month 2     |
| v2.0    | SaaS-ready with auth + billing              | Month 3-4   |

---

## 🧠 FUTURE ADVANCED FEATURES

- [ ] Auto hook rewriting (LLM rewrites first 3 seconds)
- [ ] Face detection + auto-zoom on speaker
- [ ] Scene change detection for natural cut points
- [ ] Retention scoring model (predict viral potential)
- [ ] Trend-based hashtag generation (scrape trending topics)
- [ ] AI thumbnail generator
- [ ] A/B testing for captions
- [ ] Multi-language subtitle support
- [ ] Voice cloning for dubbed versions

---

## 🔥 BETA LAUNCH STRATEGY

### Content Niches (High RPM, Low Competition)
1. **Motivational / Self-improvement** — Always viral, massive audience
2. **AI & Tech news** — Trending, high CPM
3. **Finance / Crypto** — High RPM ($15–$30 CPM)
4. **Gaming highlights** — Huge volume, easy to clip
5. **Podcast highlights** — Endless content supply

### Daily Workflow (Beta)
1. Find 2–3 trending long-form videos in your niche
2. Run through pipeline → get 6–15 clips
3. Review & select top 5–10
4. Upload manually to YouTube Shorts, Instagram Reels, TikTok
5. Track views/engagement in a simple spreadsheet
6. Iterate on prompts based on performance

### Growth Targets
- **Week 1–2:** Setup + first clips, learn the workflow
- **Month 1:** 5 shorts/day, 100–500 views per short
- **Month 2:** 10 shorts/day, optimize for retention
- **Month 3:** $2–$5/day revenue, start API uploads
- **Month 4+:** $5–$10/day, consider SaaS pivot

---

> **Remember:** The goal is **leverage through automation**. Every hour spent building this system saves 10+ hours of manual work per week. Start simple, iterate fast, and let the data guide your optimization.
