import os
import json
from openai import OpenAI
from typing import Dict, Any, Optional

MODEL = "gpt-4o"

def get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=api_key)

def _call_openai_api(prompt: str, temperature: float = 0.7) -> str:
    """Makes a call to OpenAI Chat Completions API with JSON response format."""
    client = get_client()
    
    print(f"    📡 Sending request to {MODEL} (this usually takes 10-20 seconds)...")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a world-class short-form content strategist and scriptwriter. Always respond with valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        response_format={"type": "json_object"}
    )
    print("    📥 Response received!")
    
    content = response.choices[0].message.content
    if not content:
        raise ValueError("OpenAI returned empty content")
    return content


# ─── Stage 1: Content Strategy ──────────────────────────────────────────────

def _generate_strategy(
    topic: str,
    tone: str,
    target_duration_sec: int,
    audience: Optional[str] = None,
    goal: Optional[str] = None,
    hook_style: Optional[str] = None
) -> Dict[str, Any]:
    """
    Stage 1: Generate a content strategy before writing the script.
    """
    direction_lines = ""
    if audience:
        direction_lines += f"\n- Target Audience: {audience}"
    if goal:
        direction_lines += f"\n- Primary Goal: {goal}"
    if hook_style:
        direction_lines += f"\n- Preferred Hook Style: {hook_style} (use this hook type)"

    prompt = f"""You are a top 1% short-form content strategist specializing in viral TikTok, YouTube Shorts, and Instagram Reels.

Analyze this content brief and create a strategic plan:

BRIEF:
- Topic: "{topic}"
- Tone: {tone}
- Target Duration: {target_duration_sec} seconds
- Format: Faceless video with stock footage + voiceover{direction_lines}

Your job is to define the STRATEGY before any script is written.

Think about:
1. Who is the target audience? What's their core pain point or curiosity?
2. What's the best hook type for this topic? Choose ONE:
   - Shock stat ("90% of people don't know...")
   - Curiosity gap ("There's a reason why X happens...")
   - Myth bust ("Everything you've been told about X is wrong")
   - Direct callout ("If you're still doing X, stop")
   - Secret reveal ("The thing nobody tells you about X")
   - Pattern interrupt (unexpected visual/audio opening)
   - Fear trigger ("This might be happening to you right now")
   - Identity challenge ("Only 1% of people know this")
3. What emotional progression works best? (e.g., shock to intrigue to value to urgency)
4. How many scenes should there be? (3-6 scenes for a {target_duration_sec}s video)
5. What makes this topic shareable?

Return ONLY valid raw JSON (no markdown, no explanation):
{{
  "target_audience": "Who this video is for",
  "pain_point": "Core problem or curiosity being addressed",
  "hook_type": "The chosen hook type from the list above",
  "hook_angle": "Specific angle for the hook (1 sentence)",
  "emotional_arc": ["emotion1", "emotion2", "emotion3", "emotion4"],
  "scene_count": 4,
  "shareability_factor": "Why someone would share this",
  "content_angle": "The unique angle or perspective for this topic"
}}"""

    print("🧠 Stage 1: Generating content strategy...")

    content = _call_openai_api(prompt, temperature=0.8)
    content = content.replace("```json", "").replace("```", "").strip()

    try:
        strategy = json.loads(content)
        arc = " → ".join(strategy.get("emotional_arc", []))
        print(f"  ✅ Strategy: {strategy.get('hook_type', 'unknown')} hook | {strategy.get('scene_count', '?')} scenes | Arc: {arc}")
        return strategy
    except json.JSONDecodeError as e:
        print(f"  ❌ Failed to parse strategy JSON: {content}")
        raise ValueError(f"Invalid JSON from strategy stage: {e}")


# ─── Stage 2: Script Generation ─────────────────────────────────────────────

def _generate_script_from_strategy(
    topic: str,
    tone: str,
    target_duration_sec: int,
    strategy: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Stage 2: Generate the actual script using the strategy as a creative brief.
    """
    emotional_arc = " → ".join(strategy.get("emotional_arc", ["curious", "intrigued", "convinced", "motivated"]))
    scene_count = strategy.get("scene_count", 4)

    prompt = f"""You are an elite viral short-form scriptwriter. You write scripts that get millions of views on TikTok, YouTube Shorts, and Instagram Reels.

You have been given a CREATIVE BRIEF from your strategist. Follow it precisely.

CREATIVE BRIEF:
- Topic: "{topic}"
- Tone: {tone}
- Target Duration: {target_duration_sec} seconds
- Target Audience: {strategy.get("target_audience", "general audience")}
- Pain Point: {strategy.get("pain_point", "general curiosity")}
- Hook Type: {strategy.get("hook_type", "curiosity gap")}
- Hook Angle: {strategy.get("hook_angle", "surprising perspective")}
- Emotional Arc: {emotional_arc}
- Content Angle: {strategy.get("content_angle", "unique perspective")}
- Number of Scenes: {scene_count}

SCRIPT RULES:
1. HOOK: Must be 1-2 punchy sentences using the "{strategy.get("hook_type", "curiosity gap")}" hook type. NO generic "Did you know" openings. Make it impossible to scroll past.
2. SCENES: Write exactly {scene_count} scenes. Each scene should advance the emotional arc ({emotional_arc}).
3. PACING: Short, punchy sentences. Never more than 2 sentences per scene. Each scene should feel like a mini-revelation.
4. VISUAL KEYWORDS: Give 2-3 specific, searchable stock footage terms per scene. Think cinematically.
5. CTA: End with something that creates a loop (makes them want to rewatch) OR a strong follow CTA. Not both.
6. DURATION: Each scene should be 3-7 seconds. Total should roughly add up to {target_duration_sec} seconds.
7. EMOTION TAGS: Each scene's emotion should follow the arc: {emotional_arc}.

Return ONLY valid raw JSON (no markdown, no explanation):
{{
  "title": "Short, curiosity-driven title (max 8 words)",
  "hook": "The opening hook (1-2 sentences, {strategy.get("hook_type", "curiosity gap")} style)",
  "scenes": [
    {{
      "text": "Spoken script for this scene (1-2 sentences)",
      "duration": 5,
      "visual_keyword": "2-3 cinematic stock search terms",
      "emotion": "emotion from the arc"
    }}
  ],
  "cta": "Looping ending or follow CTA"
}}"""

    print("✍️  Stage 2: Writing script from strategy...")

    content = _call_openai_api(prompt, temperature=0.7)
    content = content.replace("```json", "").replace("```", "").strip()

    try:
        script = json.loads(content)
        print(f"  ✅ Script: \"{script.get('title', 'Untitled')}\" | {len(script.get('scenes', []))} scenes")
        return script
    except json.JSONDecodeError as e:
        print(f"  ❌ Failed to parse script JSON: {content}")
        raise ValueError(f"Invalid JSON from script stage: {e}")


# ─── Public API (same signature as before) ──────────────────────────────────

def generate_script(
    topic: str,
    tone: str = "informative",
    target_duration_sec: int = 45,
    audience: Optional[str] = None,
    goal: Optional[str] = None,
    hook_style: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a structured JSON script for a faceless video using a 2-stage OpenAI pipeline.
    """
    # Stage 1: Strategy
    strategy = _generate_strategy(topic, tone, target_duration_sec, audience, goal, hook_style)

    # Stage 2: Script
    script_data = _generate_script_from_strategy(topic, tone, target_duration_sec, strategy)

    # Attach strategy metadata for debugging/analysis
    script_data["_strategy"] = strategy

    print(f"\n🎬 Script generation complete: \"{script_data.get('title', 'Untitled')}\"")
    return script_data
