import time
from app.services.faceless.script_generator import _call_gemini_api

prompt = '''You are a top 1% short-form content strategist specializing in viral TikTok, YouTube Shorts, and Instagram Reels.

Analyze this content brief and create a strategic plan:

BRIEF:
- Topic: "The Japanese urban legend of the slit-mouthed woman"
- Tone: dark mysterious
- Target Duration: 45 seconds
- Format: Faceless video with stock footage + voiceover
- Target Audience: Gen Z horror lovers
- Primary Goal: maximize retention and rewatches
- Preferred Hook Style: curiosity gap (use this hook type)

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
4. How many scenes should there be? (3-6 scenes for a 45s video)
5. What makes this topic shareable?

Return ONLY valid raw JSON (no markdown, no explanation):
{
  "target_audience": "Who this video is for",
  "pain_point": "Core problem or curiosity being addressed",
  "hook_type": "The chosen hook type from the list above",
  "hook_angle": "Specific angle for the hook (1 sentence)",
  "emotional_arc": ["emotion1", "emotion2", "emotion3", "emotion4"],
  "scene_count": 4,
  "shareability_factor": "Why someone would share this",
  "content_angle": "The unique angle or perspective for this topic"
}'''

print('Sending request to Gemini... waiting for response.')
start_time = time.time()
try:
    content = _call_gemini_api(prompt, temperature=0.8)
    elapsed = time.time() - start_time
    print(f'Done! Took {elapsed:.2f} seconds')
    print('Content:', content)
except Exception as e:
    print('Error:', e)
