import os
import google.generativeai as genai

def setup_gemini():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')

def generate_caption(clip_transcript: str) -> str:
    """Generate viral captions with hashtags for a single clip across multiple platforms."""
    model = setup_gemini()
    
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
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.8,
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"Failed to generate caption: {e}")
        return "Caption failed to generate. #fail"
