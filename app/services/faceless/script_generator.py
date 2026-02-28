import os
import json
from openai import OpenAI
from typing import Dict, Any

def get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=api_key)

def generate_script(topic: str, tone: str = "informative", target_duration_sec: int = 45) -> Dict[str, Any]:
    """
    Generates a structured JSON script for a faceless video.
    """
    client = get_client()
    
    prompt = f"""
You are an expert viral short-form faceless video scriptwriter for TikTok, YouTube Shorts, and Instagram Reels.

Write a script for a {target_duration_sec}-second vertical video about: "{topic}"
The tone should be: {tone}.

Rules:
1. The first 3 seconds must be a strong hook that grabs immediate attention or poses a compelling problem/question.
2. Use conversational, punchy writing style. Keep sentences short.
3. The ending should have a natural loop or a strong CTA that drives rewatches/follows.
4. Each scene needs a visual keyword (for searching stock footage on Pexels) and an emotion tag.
5. The total spoken text should be roughly {target_duration_sec * 2.5} words (assuming ~150 words per minute).

Return ONLY a valid, raw JSON object (NO markdown formatting or ```json blocks) strictly following this schema:
{{
  "title": "Short catchy title",
  "hook": "The first 3 seconds",
  "scenes": [
    {{
      "text": "Spoken text for this scene",
      "duration": 5,
      "visual_keyword": "one or two search terms (e.g., technology future)",
      "emotion": "serious"
    }}
  ],
  "cta": "Call to action at the end"
}}
"""

    print(f"Generating script for topic: '{topic}' with tone: {tone}")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that strictly outputs JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        response_format={ "type": "json_object" }
    )
    
    content = response.choices[0].message.content
    if not content:
        raise ValueError("Empty response from OpenAI.")
    
    data = json.loads(content)
    print("✅ Script generated successfully")
    return data
