import os
from google import genai

# Models to try in order of preference
MODELS = ["gemini-2.5-flash", "gemini-2.0-flash"]

def get_client():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    return genai.Client(api_key=api_key)

def generate_caption(clip_transcript: str) -> str:
    """Generate viral captions with hashtags for a single clip across multiple platforms."""
    client = get_client()
    
    prompt = f"""
Generate a viral caption for this short video clip, customized for three platforms: YouTube Shorts, TikTok, and Instagram Reels.

Rules for EACH platform:
- Under 150 characters for the main text.
- Include a strong hook or question.
- Use a conversational, engaging tone.
- Add exactly 5 relevant trending hashtags (1 broad, 4 niche).

Format your response EXACTLY like this:
[YouTube Shorts]
(caption here)

[TikTok]
(caption here)

[Instagram Reels]
(caption here)

Clip Transcript:
"{clip_transcript}"
"""
    
    for model_name in MODELS:
        try:
            print(f"Caption: trying model {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "temperature": 0.8,
                }
            )
            print(f"✅ Caption success with model: {model_name}")
            return response.text.strip()
        except Exception as e:
            print(f"❌ Caption model {model_name} failed: {e}")
            continue
    
    return "Caption failed to generate. #fail"
