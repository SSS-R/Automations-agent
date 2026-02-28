import os
from openai import OpenAI
from typing import Optional

def get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set. Please add it, or pass use_edge_tts=True to use free edge-tts.")
    return OpenAI(api_key=api_key)

def generate_voice(text: str, output_path: str, voice: str = "onyx", use_edge_tts: bool = False) -> str:
    """
    Generates TTS audio from text.
    If use_edge_tts=True, uses the free Edge-TTS API.
    Otherwise uses OpenAI's tts-1 model.
    Saves the output to output_path.
    Returns the absolute path to the generated audio file.
    """
    abs_path = os.path.abspath(output_path)
    print(f"Generating voiceover for text: '{text[:30]}...' -> {abs_path}")
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    
    if use_edge_tts:
        import asyncio
        import edge_tts
        edge_voice = "en-US-ChristopherNeural"
        
        async def _generate():
            communicate = edge_tts.Communicate(text, edge_voice)
            await communicate.save(abs_path)
            
        asyncio.run(_generate())
        print(f"✅ Voiceover (Edge-TTS) generated to {abs_path}")
        return abs_path

    # Only initialize OpenAI client if we actually need it
    client = get_client()
    
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    
    response.stream_to_file(abs_path)
    print(f"✅ Voiceover (OpenAI) generated to {abs_path}")
    
    return abs_path
