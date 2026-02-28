import os
import json
from datetime import datetime
from slugify import slugify
from .script_generator import generate_script
from .asset_fetcher import fetch_stock_video
from .voice_generator import generate_voice

def faceless_pipeline(topic: str, tone: str = "informative", duration: int = 45, template: str = "minimal"):
    """
    End-to-end testing of the faceless video generation foundation.
    1. Generate script (GPT-4o)
    2. Fetch stock assets (Pexels)
    3. Generate voiceover (OpenAI TTS)
    """
    print(f"🚀 Starting Faceless Pipeline for topic: '{topic}'")
    
    # 1. Setup Output Directory
    slug = slugify(topic)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.abspath(f"output/faceless/{slug}-{timestamp}")
    assets_dir = os.path.join(output_dir, "assets")
    audio_dir = os.path.join(output_dir, "audio")
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    
    print(f"📁 Created output directory: {output_dir}")
    
    # 2. Generate Script
    print("\n📝 Phase 1: Generating Script")
    script_data = generate_script(topic, tone, duration)
    
    script_path = os.path.join(output_dir, "script.json")
    with open(script_path, "w") as f:
        json.dump(script_data, f, indent=2)
    print(f"✅ Script saved to {script_path}")
    
    # 3. Process Scenes (Assets + Voice)
    print("\n🎬 Phase 2 & 3: Fetching Assets & Generating Voice")
    
    for i, scene in enumerate(script_data.get("scenes", [])):
        scene_id = f"scene_{i+1:02d}"
        print(f"\n--- Processing {scene_id} ---")
        
        # Voice
        text = scene.get("text", "")
        if text:
            audio_path = os.path.join(audio_dir, f"{scene_id}.mp3")
            generate_voice(text, audio_path)
            # Update script data with generated audio path (useful for Remotion later)
            scene["audio_file"] = os.path.basename(audio_path)
            
        # Assets
        keyword = scene.get("visual_keyword", "")
        if keyword:
            asset_path = os.path.join(assets_dir, f"{scene_id}.mp4")
            downloaded = fetch_stock_video(keyword, asset_path)
            if downloaded:
                scene["asset_file"] = os.path.basename(asset_path)
                
    # Also generate audio for hook and CTA if they exist as separate text chunks not in scenes array
    # Looking at our schema, hook is separate text
    hook_text = script_data.get("hook", "")
    if hook_text:
        print("\n--- Processing Hook Audio ---")
        hook_audio_path = os.path.join(audio_dir, "hook.mp3")
        generate_voice(hook_text, hook_audio_path)
        script_data["hook_audio_file"] = "hook.mp3"
        
    cta_text = script_data.get("cta", "")
    if cta_text:
        print("\n--- Processing CTA Audio ---")
        cta_audio_path = os.path.join(audio_dir, "cta.mp3")
        generate_voice(cta_text, cta_audio_path)
        script_data["cta_audio_file"] = "cta.mp3"

    # Save the updated script data with file references
    with open(script_path, "w") as f:
        json.dump(script_data, f, indent=2)

    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, 'w') as f:
         json.dump({
             "topic": topic,
             "tone": tone,
             "target_duration": duration,
             "template": template,
             "created_at": timestamp
         }, f, indent=2)

    print(f"\n✅ Phase F1 Foundation Pipeline completed for '{topic}'!")
    return output_dir

if __name__ == "__main__":
    # Test script if run directly
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "The future of Artificial Intelligence"
    faceless_pipeline(topic, duration=20)
