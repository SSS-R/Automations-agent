import os
import json
import google.generativeai as genai
from typing import List, Dict

# Assuming API key is set via python-dotenv in main.py
def setup_gemini():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    genai.configure(api_key=api_key)
    
    # Use Gemini 2.0 Flash as it represents the best free tier speed/cost ratio
    return genai.GenerativeModel('gemini-2.0-flash')

def detect_highlights(formatted_transcript: str) -> List[Dict]:
    """
    Passes a formatted timestamp string to Gemini to detect 3-5 viral highlights.
    Returns a structured dictionary list.
    """
    model = setup_gemini()
    
    prompt = f"""
You are an expert viral short-form content editor for platforms like TikTok, YouTube Shorts, and Instagram Reels.

Analyze this timestamped transcript and select the 3 to 5 most engaging, high-retention segments (between 20 and 60 seconds each) that would make perfect viral shorts.

Prioritize:
1. Strong hooks (the first 3 seconds MUST grab immediate attention or pose a compelling problem/question).
2. Emotional peaks, surprising facts, or controversial/bold statements.
3. Highly actionable advice.
4. Complete, cohesive thoughts.

The transcript format is [HH:MM:SS → HH:MM:SS] Text.

Return ONLY a valid, raw JSON array (NO markdown formatting or ```json blocks) where each object strictly follows this schema:
[
  {{
    "start": "00:02:10",
    "end": "00:02:45",
    "hook": "Suggested on-screen text for the first 3 seconds",
    "reason": "Brief explanation of why this segment is highly engaging",
    "viral_score": 8
  }}
]

Transcript:
{formatted_transcript}
"""

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.7,
            response_mime_type="application/json"
        )
    )
    
    try:
        data = json.loads(response.text)
        # Sort by viral score descending to grab the very best first
        return sorted(data, key=lambda x: x.get('viral_score', 0), reverse=True)
    except Exception as e:
        print(f"Failed to parse LLM highlight JSON: {e}")
        print("Raw response:", response.text)
        return []

def timestamp_to_seconds(ts: str) -> float:
    """Convert HH:MM:SS or MM:SS to total float seconds."""
    parts = ts.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(ts)
