---
name: remotion-video-editing
description: How to use Remotion for programmatic video editing — setup, captions, templates, and rendering
---

# Remotion Video Editing Skill

## Overview

Remotion is a React-based framework for creating videos programmatically. Instead of manually editing in Premiere/After Effects, you write React components that render to MP4.

**GitHub:** https://github.com/remotion-dev/remotion
**Docs:** https://remotion.dev/docs
**License:** Free for personal use

---

## Quick Setup

### 1. Prerequisites
- Node.js 18+ installed
- FFmpeg installed and in PATH

### 2. Install Remotion in Your Project

```bash
# Create a new Remotion project
npx create-video@latest

# OR add to existing project
npm i --save-exact remotion @remotion/cli @remotion/player
```

### 3. Key Packages

| Package | Purpose |
|---------|---------|
| `remotion` | Core framework |
| `@remotion/cli` | CLI for rendering |
| `@remotion/captions` | Caption/subtitle utilities |
| `@remotion/install-whisper-cpp` | Local transcription (FREE) |
| `@remotion/player` | Browser preview player |
| `@remotion/lambda` | Cloud rendering (optional) |

---

## Local Transcription with Whisper.cpp (FREE)

Instead of paying for Whisper API, use `@remotion/install-whisper-cpp`:

```bash
npm i --save-exact @remotion/install-whisper-cpp
```

```typescript
import path from 'path';
import { installWhisperCpp, downloadWhisperModel, transcribe, toCaptions } from '@remotion/install-whisper-cpp';

const whisperPath = path.join(process.cwd(), 'whisper.cpp');

// One-time setup (downloads ~1.5GB model)
await installWhisperCpp({ to: whisperPath, version: '1.5.5' });
await downloadWhisperModel({ model: 'medium.en', folder: whisperPath });

// Convert audio to 16KHz WAV first (required by whisper.cpp)
// ffmpeg -i input.mp4 -ar 16000 audio.wav -y

// Transcribe with token-level timestamps
const whisperOutput = await transcribe({
  model: 'medium.en',
  whisperPath,
  whisperCppVersion: '1.5.5',
  inputPath: './audio.wav',
  tokenLevelTimestamps: true,
});

// Convert to Remotion Caption format
const { captions } = toCaptions({ whisperCppOutput: whisperOutput });

// Save captions
import fs from 'fs';
fs.writeFileSync('captions.json', JSON.stringify(captions, null, 2));
```

**Models available:** `tiny`, `tiny.en`, `base`, `base.en`, `small`, `small.en`, `medium`, `medium.en`, `large-v3`

> Use `medium.en` for best quality/speed balance on English content. Use `small.en` for faster processing.

---

## TikTok-Style Animated Captions

```bash
npm i --save-exact @remotion/captions
```

### Import and use captions

```typescript
import { createTikTokStyleCaptions } from '@remotion/captions';
import type { Caption } from '@remotion/captions';

// Load captions from transcription
const captions: Caption[] = JSON.parse(fs.readFileSync('captions.json', 'utf-8'));

// Create TikTok-style word-by-word captions
const { pages } = createTikTokStyleCaptions({
  captions,
  combineTokensWithinMilliseconds: 800,  // Group words appearing within 800ms
});
```

### Render captions in a React component

```tsx
import React from 'react';
import { useCurrentFrame, useVideoConfig, Sequence } from 'remotion';

export const AnimatedCaptions: React.FC<{pages: any[]}> = ({ pages }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTimeMs = (frame / fps) * 1000;

  return (
    <div style={{
      position: 'absolute',
      bottom: 150,
      left: 0,
      right: 0,
      textAlign: 'center',
      padding: '0 40px',
    }}>
      {pages.map((page, i) => {
        if (currentTimeMs < page.startMs || currentTimeMs > page.endMs) return null;
        return (
          <div key={i} style={{ fontSize: 48, fontWeight: 'bold', color: 'white', textShadow: '2px 2px 8px rgba(0,0,0,0.8)' }}>
            {page.tokens.map((token: any, j: number) => (
              <span key={j} style={{
                color: currentTimeMs >= token.fromMs ? '#FFD700' : 'white',
                transition: 'color 0.1s',
              }}>
                {token.text}
              </span>
            ))}
          </div>
        );
      })}
    </div>
  );
};
```

---

## Creating Short-Form Video Templates

### Basic Short Clip Component

```tsx
import { AbsoluteFill, Video, Sequence, useCurrentFrame, useVideoConfig } from 'remotion';

interface ShortClipProps {
  videoSrc: string;
  captions: any[];
  hookText: string;
}

export const ShortClip: React.FC<ShortClipProps> = ({ videoSrc, captions, hookText }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: 'black' }}>
      {/* Background video */}
      <Video src={videoSrc} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />

      {/* Hook text overlay (first 3 seconds) */}
      <Sequence durationInFrames={fps * 3}>
        <div style={{
          position: 'absolute',
          top: '15%',
          left: '10%',
          right: '10%',
          fontSize: 42,
          fontWeight: 900,
          color: 'white',
          textAlign: 'center',
          textShadow: '3px 3px 10px rgba(0,0,0,0.9)',
          opacity: Math.min(1, frame / (fps * 0.3)),
        }}>
          {hookText}
        </div>
      </Sequence>

      {/* Animated captions */}
      <AnimatedCaptions pages={captions} />

      {/* Progress bar at bottom */}
      <div style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        height: 4,
        width: `${(frame / durationInFrames) * 100}%`,
        backgroundColor: '#FF0050',
      }} />
    </AbsoluteFill>
  );
};
```

### Register the composition

```tsx
// src/Root.tsx
import { Composition } from 'remotion';
import { ShortClip } from './ShortClip';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="ShortClip"
      component={ShortClip}
      durationInFrames={30 * 30}  // 30 seconds at 30fps
      fps={30}
      width={1080}
      height={1920}  // 9:16 vertical
      defaultProps={{
        videoSrc: '',
        captions: [],
        hookText: '',
      }}
    />
  );
};
```

---

## Rendering Videos

### CLI Rendering

```bash
# Preview in browser
npx remotion studio

# Render to MP4
npx remotion render src/index.ts ShortClip out/clip.mp4

# Render with custom props
npx remotion render src/index.ts ShortClip out/clip.mp4 \
  --props='{"videoSrc": "public/clip_01.mp4", "hookText": "You won'\''t believe this..."}'

# Render with quality settings
npx remotion render src/index.ts ShortClip out/clip.mp4 \
  --codec=h264 \
  --crf=18 \
  --pixel-format=yuv420p
```

### Programmatic Rendering (Node.js)

```typescript
import { bundle } from '@remotion/bundler';
import { renderMedia, selectComposition } from '@remotion/renderer';

const bundled = await bundle({ entryPoint: './src/index.ts' });

const composition = await selectComposition({
  serveUrl: bundled,
  id: 'ShortClip',
  inputProps: {
    videoSrc: 'public/clip_01.mp4',
    captions: captionsData,
    hookText: 'This changed everything...',
  },
});

await renderMedia({
  composition,
  serveUrl: bundled,
  codec: 'h264',
  outputLocation: 'out/clip_01_final.mp4',
});
```

---

## Template Ideas for Short-Form Content

| Template | Description | Use Case |
|----------|-------------|----------|
| **TikTok Captions** | Word-by-word animated subtitles | All short clips |
| **Hook + Content** | Bold hook text → content with captions | Motivational, tips |
| **Split Screen** | Video top, text/captions bottom | Educational, podcast |
| **Zoom Effect** | Ken Burns zoom on key moments | Dramatic moments |
| **Quote Card** | Animated text on gradient background | Quote pages |
| **News Style** | Lower third + headline banner | AI/Tech news |
| **Before/After** | Side-by-side comparison | Tutorials |

---

## Integration with Python Pipeline

The Python pipeline handles downloading, audio extraction, and highlight detection. Remotion handles the final video rendering:

```
Python Pipeline (FastAPI)
  1. Download video (yt-dlp)
  2. Extract audio (FFmpeg)
  3. Detect highlights (LLM)
  4. Generate clip timestamps
       ↓ (writes JSON config)
Remotion Pipeline (Node.js)
  5. Transcribe audio (whisper.cpp — FREE)
  6. Generate animated captions
  7. Apply template (hook, overlays, progress bar)
  8. Render final MP4
       ↓
Python Pipeline (FastAPI)
  9. Generate text captions/hashtags (LLM)
  10. Organize output
```

### Bridge Script (Python calls Node.js)

```python
import subprocess
import json

def render_clip_with_remotion(clip_config: dict, output_path: str):
    """Render a clip using Remotion from Python."""
    props = json.dumps(clip_config)
    result = subprocess.run([
        'npx', 'remotion', 'render',
        'src/index.ts', 'ShortClip',
        output_path,
        f'--props={props}',
        '--codec=h264',
        '--crf=18',
    ], capture_output=True, text=True, cwd='./remotion-editor')
    
    if result.returncode != 0:
        raise Exception(f"Remotion render failed: {result.stderr}")
    return output_path
```

---

## Cost Summary

| Component | Cost |
|-----------|------|
| Remotion (personal use) | **Free** |
| Whisper.cpp (local) | **Free** |
| Node.js | **Free** |
| FFmpeg | **Free** |
| **Total** | **$0** |

> Remotion is free for personal use and companies with less than $1M annual revenue. Perfect for beta/personal monetization phase.

---

## Useful Links

- **Docs:** https://remotion.dev/docs
- **GitHub:** https://github.com/remotion-dev/remotion
- **Captions docs:** https://remotion.dev/docs/captions
- **Whisper.cpp docs:** https://remotion.dev/docs/install-whisper-cpp
- **TikTok template:** https://remotion.dev/templates/tiktok
- **Examples:** https://github.com/remotion-dev/remotion/tree/main/packages/example
