# 🚀 Extension: AI Faceless Video Generation Engine

> **Status:** Roadmap — Not yet implemented  
> **Depends on:** Existing clipping pipeline (Phase 1 of `plan.md`)

---

## 🎯 Vision

Extend the Automations Agent with a **second pipeline**: fully generating faceless short-form videos from a topic input using Remotion templates.

| Pipeline | Input | Output |
|----------|-------|--------|
| **Clipping** (existing) | Long video URL | Viral short clips from highlights |
| **Faceless** (this extension) | Topic / idea | Original animated vertical video |

**Goal:** Generate high-quality, animated, branded vertical videos optimized for Shorts/Reels — with zero stock footage dependency if needed.

---

## 🧠 Architecture

```
Topic Input (text)
       ↓
┌──────────────────────────┐
│  1. Script Generator     │  ← GPT-4o generates structured JSON script
│     (GPT-4o)             │     with hook, scenes, CTA
└──────────┬───────────────┘
           ↓
┌──────────────────────────┐
│  2. Scene Splitter       │  ← Split script into timed scenes with
│     + Asset Tagger       │     emotion tags and visual keywords
└──────────┬───────────────┘
           ↓
┌──────────────────────────┐
│  3. Asset Fetcher        │  ← Pexels/Pixabay API → 9:16 stock video/images
│     (Stock API)          │     Fallback: generated backgrounds / gradients
└──────────┬───────────────┘
           ↓
┌──────────────────────────┐
│  4. Voice Generator      │  ← OpenAI TTS (tts-1) — premium quality voices
│     (OpenAI TTS)         │     Output: per-scene audio segments
└──────────┬───────────────┘
           ↓
┌──────────────────────────┐
│  5. Remotion Renderer    │  ← Compose video from template + assets + audio
│     (React → MP4)        │     Animated subtitles, transitions, branding
└──────────┬───────────────┘
           ↓
┌──────────────────────────┐
│  6. Caption Generator    │  ← GPT-4o-mini generates platform-optimized
│     (GPT-4o-mini)        │     captions + hashtags
└──────────┘
```

---

## 📦 Core Components

### 1. Script Generation Engine (`app/services/faceless/script_generator.py`)

**Input:** Topic string, tone (motivational/informative/dramatic), target duration (30–60s)

**Output:** Structured JSON:
```json
{
  "title": "Why AI Will Change Everything",
  "hook": "In 10 years, 80% of jobs won't exist.",
  "scenes": [
    {
      "text": "AI is replacing jobs faster than you think",
      "duration": 5,
      "visual_keyword": "technology future robot",
      "emotion": "serious"
    },
    {
      "text": "But here's what no one tells you...",
      "duration": 6,
      "visual_keyword": "person thinking mystery",
      "emotion": "suspense"
    }
  ],
  "cta": "Follow for more AI insights"
}
```

**Requirements:**
- First 3 seconds must be a strong hook
- Conversational, punchy writing style
- Loopable ending (CTA drives rewatches)
- Each scene has emotion + visual keyword metadata

> [!TIP]
> Reuse the existing `highlighter.py` LLM call pattern — same OpenAI client, just different prompts and model set to `gpt-4o`.

---

### 2. Asset Fetching Layer (`app/services/faceless/asset_fetcher.py`)

**Sources (in priority order):**

| Source | Cost | Quality | Notes |
|--------|------|---------|-------|
| Pexels API | Free (API key) | High | 200 req/hr, 9:16 filter available |
| Pixabay API | Free (API key) | Medium | Good fallback |
| Local stock library | Free | Variable | Cache downloaded assets for reuse |
| Gradient/color backgrounds | Free | Consistent | Rendered by Remotion as fallback |

**Logic:**
1. Search Pexels for `visual_keyword` → download 9:16 video/image
2. Fallback to Pixabay if Pexels has no results
3. Fallback to a Remotion-rendered gradient/particle background
4. Cache all downloaded assets in `/assets/stock/` for reuse

> [!IMPORTANT]
> Always download **vertical (9:16)** assets. Pexels API supports orientation filters. Pixabay does not — crop to 9:16 via FFmpeg after download.

---

### 3. Voice Engine (`app/services/faceless/voice_generator.py`)

**Engine:** OpenAI TTS (`tts-1`)

| Property | Value |
|----------|-------|
| **API** | OpenAI TTS (`tts-1`) |
| **Cost** | $15 per 1M characters (~$0.01 per video) |
| **Quality** | Excellent — natural, expressive |
| **Voices** | `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer` |
| **Output** | MP3 / WAV per scene |

**Implementation:**
```python
from openai import OpenAI

client = OpenAI()
response = client.audio.speech.create(
    model="tts-1",
    voice="onyx",  # deep, authoritative — great for faceless content
    input="AI is replacing jobs faster than you think."
)
response.stream_to_file("scene_01.mp3")
```

**Output:** Per-scene MP3 audio files + merged full narration track.

> [!NOTE]
> Uses the same `OPENAI_API_KEY` already in your `.env` — no new keys needed.

---

### 4. Remotion Faceless Templates (`remotion-editor/src/faceless/`)

> [!IMPORTANT]
> This builds ON TOP of the existing `remotion-editor/`. We add a new `faceless/` directory — we do NOT touch the existing clipping components (`ShortClip.tsx`, `AnimatedCaptions.tsx`).

**New Remotion compositions:**

```
remotion-editor/src/
  ├── ShortClip.tsx              # (existing — clipping pipeline)
  ├── AnimatedCaptions.tsx       # (existing — clipping pipeline)
  ├── Root.tsx                   # (updated — register new compositions)
  └── faceless/
      ├── FacelessVideo.tsx      # Main faceless composition (orchestrates scenes)
      ├── HookScene.tsx          # First 3s — large animated hook text
      ├── ContentScene.tsx       # Main scene — stock BG + animated text overlay
      ├── CTAScene.tsx           # Ending CTA screen
      ├── transitions.tsx        # Shared transition effects (fade, slide, zoom)
      └── templates/
          ├── MinimalTemplate.tsx # Clean, white text on dark BG
          ├── BoldTemplate.tsx   # Large bold colorful text, motion graphics
          └── TechTemplate.tsx   # Futuristic/tech aesthetics
```

**Rendering features:**
- 9:16 vertical (1080×1920)
- Word-by-word animated subtitles (reuse existing `AnimatedCaptions.tsx` logic)
- Smooth scene transitions (cross-fade, slide, zoom)
- Auto-zoom / Ken Burns effect on stock footage
- Branded color themes per template
- Dynamic text animations (typewriter, pop-in, scale)

---

### 5. Faceless Pipeline Orchestrator (`app/services/faceless/pipeline.py`)

Ties everything together:

```python
def faceless_pipeline(topic: str, tone: str = "informative", duration: int = 45, template: str = "minimal"):
    """
    End-to-end faceless video generation.
    1. Generate script (GPT-4o)
    2. Fetch stock assets (Pexels)
    3. Generate voiceover (OpenAI TTS)
    4. Render video (Remotion)
    5. Generate caption (GPT-4o-mini)
    """
```

**Output structure:**
```
/output/faceless/
  /[topic-slug]-[date]/
    script.json           # Generated script
    /assets/              # Downloaded stock footage
    /audio/               # TTS audio files
    video.mp4             # Final rendered video
    caption.txt           # Platform captions + hashtags
    metadata.json         # Generation parameters
```

---

### 6. Caption Generator

Reuse existing `captioner.py` with a modified prompt for faceless content (no transcript context — use the generated script instead).

---

## 🗓️ Development Roadmap

### Phase F1 — Foundation (Week 1)

- [ ] Create `app/services/faceless/` module structure
- [ ] Implement `script_generator.py` — GPT-4o script generation with structured JSON output
- [ ] Implement `asset_fetcher.py` — Pexels API integration with 9:16 filter
- [ ] Implement `voice_generator.py` — OpenAI TTS (`tts-1`) integration
- [ ] Test: topic → script JSON → assets downloaded → audio generated

**Deliverable:** All data inputs ready for rendering (script + assets + audio).

---

### Phase F2 — Remotion Faceless Templates (Week 2)

- [ ] Create `FacelessVideo.tsx` — main composition that takes script JSON as props
- [ ] Create `HookScene.tsx` — animated hook text (first 3 seconds)
- [ ] Create `ContentScene.tsx` — stock footage BG + text overlay with animations
- [ ] Create `CTAScene.tsx` — call-to-action ending screen
- [ ] Create `MinimalTemplate.tsx` — first template style
- [ ] Add transition effects between scenes
- [ ] Register new composition in `Root.tsx`

**Deliverable:** Remotion renders a complete faceless video from script JSON.

---

### Phase F3 — Audio Sync & Subtitles (Week 3)

- [ ] Sync TTS audio with scene durations
- [ ] Add word-level animated subtitles to faceless videos
- [ ] Auto-calculate scene durations from TTS audio length
- [ ] Implement audio crossfade between scenes

**Deliverable:** Fully narrated faceless video with animated subtitles.

---

### Phase F4 — Additional Templates & Polish (Week 4)

- [ ] Create `BoldTemplate.tsx` and `TechTemplate.tsx`
- [ ] Add template selection to the pipeline
- [ ] Add font preset system (Google Fonts)
- [ ] Add color palette/theme system
- [ ] Add Ken Burns / auto-zoom effect on stock footage
- [ ] Background music support (optional low-volume track)

**Deliverable:** Multiple selectable template styles with professional polish.

---

### Phase F5 — API & Batch Mode (Week 5)

- [ ] Add FastAPI endpoint: `POST /api/faceless/generate`
- [ ] Add batch generation (multiple topics → queue)
- [ ] Integrate with existing Celery workers
- [ ] Add template preview endpoint
- [ ] Asset cache management (reuse downloaded stock)
- [ ] Auto file cleanup for temp files

**Deliverable:** Full API-driven faceless video generation.

---

## 🔑 API Keys Required

| Service | Purpose | Cost | `.env` Key |
|---------|---------|------|------------|
| **OpenAI** (GPT-4o + TTS) | Script generation + voice | ~$0.03/video | `OPENAI_API_KEY` (already configured) |
| **Pexels** | Stock video/images | Free | `PEXELS_API_KEY` (new — [signup](https://www.pexels.com/api/)) |
| **Pixabay** | Fallback stock | Free | `PIXABAY_API_KEY` (optional — [signup](https://pixabay.com/api/docs/)) |

> [!NOTE]
> `OPENAI_API_KEY` is already in your `.env` from the clipping pipeline. Only **Pexels** requires a new (free) key.

---

## 💰 Cost Analysis — Faceless Pipeline (Premium Stack)

> [!IMPORTANT]
> **Chosen stack:** GPT-4o (scripts) + OpenAI TTS (voice) + GPT-4o-mini (captions) + Pexels (stock assets)

### Per Video Cost Breakdown (~45s faceless video)

| Step | API | Cost per Video |
|------|-----|----------------|
| **Script Generation** | GPT-4o (~1K input + 300 output tokens) | **$0.01** |
| **Stock Assets** | Pexels API | **$0** |
| **Voice / TTS** | OpenAI TTS `tts-1` (~700 chars) | **$0.01** |
| **Remotion Rendering** | Local | **$0** |
| **Subtitle Timing** | Local processing | **$0** |
| **Caption Generation** | GPT-4o-mini (~500 input + 200 output tokens) | **$0.01** |
| **Background Music** | Royalty-free (bundled) | **$0** |
| **Total per video** | | **~$0.03** |

### Monthly Projections

| Daily Output | Videos/mo | OpenAI API Cost | Notes |
|-------------|-----------|-----------------|-------|
| 3/day | 90 | **~$2.70/mo** | Light usage |
| 5/day | 150 | **~$4.50/mo** | Recommended target |
| 10/day | 300 | **~$9.00/mo** | Heavy production |
| 20/day | 600 | **~$18.00/mo** | Maximum scale |

### OpenAI API Pricing Reference

| API | Pricing | Used For |
|-----|---------|----------|
| **GPT-4o** | $2.50 / $10.00 per 1M tokens | Script generation (best hooks & scenes) |
| **GPT-4o-mini** | $0.15 / $0.60 per 1M tokens | Caption generation (cheap, good enough) |
| **OpenAI TTS** (`tts-1`) | $15 per 1M characters | Voice narration (natural quality) |
| **Pexels API** | Free (200 req/hr) | Stock video/images |

---

## 🧠 Design Decisions & Notes

### 1. Audio-Driven Scene Durations

Do NOT use fixed durations from the script JSON. **Generate TTS audio first**, measure its actual duration, then set the Remotion scene duration to match audio length + 0.5s buffer. This prevents audio-visual desync.

### 2. Gradient/Particle Fallback Backgrounds

Many topics won't have good stock footage on Pexels. The Remotion gradient/particle background fallback is a **first-class feature**, not a last resort. This enables "text-only" template styles that many viral faceless channels use.

### 3. Reuse Existing Infrastructure

- **OpenAI client** — same setup from `highlighter.py` (just change model to `gpt-4o`)
- **Remotion renderer bridge** — same `remotion_renderer.py` pattern for Python→Node
- **Caption generator** — same `captioner.py` with modified prompts
- **Pipeline pattern** — same orchestration style as `pipeline.py`
- **Output structure** — same `/output/` folder convention

### 4. Background Music Support

Add optional royalty-free background music at low volume behind TTS narration. Simple FFmpeg audio mix — low effort, high retention impact.

### 5. Template Preview System

Before full renders (which take minutes), add a quick mode that renders only the 3-second hook scene. Enables fast iteration on template choice.

### 6. Content Series / Batch Mode

Input a broad topic (e.g., "10 AI facts") → GPT-4o generates 5–10 separate video scripts → batch render all. Critical for content consistency.

---

## ⚠️ Key Architecture Decisions

### Separation of Concerns

The faceless pipeline is a **completely separate pipeline** from the clipping pipeline. They share:
- ✅ OpenAI client (GPT-4o / GPT-4o-mini)
- ✅ Remotion rendering infrastructure
- ✅ Caption generation
- ✅ Output folder structure
- ✅ FastAPI server & Celery workers

They do **NOT** share:
- ❌ Video download (faceless doesn't download videos)
- ❌ Transcription (faceless generates scripts, not transcripts)
- ❌ Highlight detection (faceless doesn't detect highlights)
- ❌ FFmpeg clipping (faceless doesn't clip existing videos)

### File Structure

```
app/services/
  ├── downloader.py          # (existing — clipping only)
  ├── transcriber.py         # (existing — clipping only)
  ├── highlighter.py         # (existing — clipping only)
  ├── clipper.py             # (existing — clipping only)
  ├── captioner.py           # (shared — both pipelines)
  ├── pipeline.py            # (existing — clipping pipeline)
  ├── remotion_renderer.py   # (shared — both pipelines)
  └── faceless/              # (NEW — faceless pipeline)
      ├── __init__.py
      ├── script_generator.py
      ├── asset_fetcher.py
      ├── voice_generator.py
      └── pipeline.py        # faceless orchestrator
```

---

## 🏁 Prerequisites Before Starting

Before building this extension, ensure:

1. [x] Clipping pipeline is functional (Phase 1 of `plan.md`)
2. [x] Remotion editor renders videos successfully
3. [x] Animated captions work in Remotion
4. [ ] Pexels API key obtained (free — [signup here](https://www.pexels.com/api/))
5. [ ] OpenAI API key has TTS access (same key, already configured)

---

## 🔥 Differentiation: Why This Will Stand Out

| Generic Faceless Tools | This Engine |
|------------------------|-------------|
| Static slideshow | Cinematic scene transitions |
| Basic white text | Word-by-word animated subtitles |
| No customization | React template system (infinite flexibility) |
| Cloud-only SaaS ($30+/mo) | Self-hosted, ~$5–9/month |
| Cookie-cutter output | Multiple branded templates |
| Manual process | Fully automated pipeline |

---

## 🚀 Future Extensions (Post-MVP)

- [ ] AI thumbnail generation for each video
- [ ] Multi-language TTS + subtitle support
- [ ] SaaS dashboard with template marketplace
- [ ] A/B testing: generate 2 versions of each video with different hooks
- [ ] Trend scraping: auto-generate videos based on trending topics
- [ ] Music library with mood-based auto-selection
- [ ] Analytics: track which templates/hooks perform best