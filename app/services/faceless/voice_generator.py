import os
from openai import OpenAI
from typing import Optional

def get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=api_key)

def generate_voice(text: str, output_path: str, voice: str = "onyx") -> str:
    """
    Generates TTS audio from text using OpenAI's tts-1 model.
    Saves the output to output_path.
    Returns the absolute path to the generated audio file.
    """
    client = get_client()
    
    abs_path = os.path.abspath(output_path)
    print(f"Generating voiceover for text: '{text[:30]}...' -> {abs_path}")
    
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    
    response.stream_to_file(abs_path)
    print(f"✅ Voiceover generated to {abs_path}")
    
    return abs_path
