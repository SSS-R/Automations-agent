import os
import json
from datetime import datetime
from slugify import slugify
from dotenv import load_dotenv

load_dotenv()
from .script_generator import generate_script
from .asset_fetcher import fetch_stock_video
from .voice_generator import generate_voice

from .audio_sync import process_audio_for_scene

def faceless_pipeline(topic: str, tone: str = "informative", duration: int = 45, template: str = "minimal", font_preset: str = "inter", color_palette: str = "default", skip_api: bool = False, audience: str = None, goal: str = None, hook_style: str = None):
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
    
    # We must expose these to Remotion's public folder so it can access them
    remotion_public_dir = os.path.abspath("remotion-editor/public/faceless_assets")
    os.makedirs(remotion_public_dir, exist_ok=True)
    
    print(f"📁 Created output directory: {output_dir}")
    
    # 2. Generate Script
    print("\n📝 Phase 1: Generating Script")
    from .script_generator import generate_script
    script_data = generate_script(topic, tone, duration, audience=audience, goal=goal, hook_style=hook_style)
        
    # Append theming data to the root of the script json to feed into remotion
    script_data["template"] = template
    script_data["font_preset"] = font_preset
    script_data["color_palette"] = color_palette
    
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
            audio_path = os.path.join(audio_dir, f"{scene_id}.wav") # Use wav for whisper compat
            from .voice_generator import generate_voice
            generate_voice(text, audio_path, use_edge_tts=skip_api)

            if os.path.exists(audio_path):
                import shutil
                public_audio_name = f"{slug}-{scene_id}.wav"
                public_audio_path = os.path.join(remotion_public_dir, public_audio_name)
                shutil.copy(audio_path, public_audio_path)
                
                scene["audio_file"] = f"faceless_assets/{public_audio_name}"
                
                # Phase F3: Dynamic duration & Subtitles
                frames, pages = process_audio_for_scene(audio_path, fps=30)
                scene["durationInFrames"] = frames
                scene["captionPages"] = pages
            else:
                # Fallback duration if audio missing and skipping API
                scene["durationInFrames"] = scene.get("duration", 4) * 30
            
        # Assets
        keyword = scene.get("visual_keyword", "")
        if keyword:
            asset_path = os.path.join(assets_dir, f"{scene_id}.mp4")
            # Always fetch stock video, Pexels API is free
            from .asset_fetcher import fetch_stock_video
            downloaded = fetch_stock_video(keyword, asset_path)
            if downloaded:
                import shutil
                public_asset_name = f"{slug}-{scene_id}.mp4"
                public_asset_path = os.path.join(remotion_public_dir, public_asset_name)
                shutil.copy(asset_path, public_asset_path)
                
                scene["asset_file"] = f"faceless_assets/{public_asset_name}"
                
    # Also generate audio for hook and CTA if they exist as separate text chunks not in scenes array
    # Looking at our schema, hook is separate text
    hook_text = script_data.get("hook", "")
    if hook_text:
        print("\n--- Processing Hook Audio ---")
        hook_audio_path = os.path.join(audio_dir, "hook.wav")
        from .voice_generator import generate_voice
        generate_voice(hook_text, hook_audio_path, use_edge_tts=skip_api)
                
        if os.path.exists(hook_audio_path):
            import shutil
            public_hook_name = f"{slug}-hook.wav"
            public_hook_path = os.path.join(remotion_public_dir, public_hook_name)
            shutil.copy(hook_audio_path, public_hook_path)
            
            script_data["hook_audio_file"] = f"faceless_assets/{public_hook_name}"
            frames, pages = process_audio_for_scene(hook_audio_path, fps=30)
            script_data["hookDurationInFrames"] = frames
            # Subtitles for hook normally aren't fully word-by-word like Main Scenes, or maybe they are
            script_data["hookCaptionPages"] = pages

    cta_text = script_data.get("cta", "")
    if cta_text:
        print("\n--- Processing CTA Audio ---")
        cta_audio_path = os.path.join(audio_dir, "cta.wav")
        from .voice_generator import generate_voice
        generate_voice(cta_text, cta_audio_path, use_edge_tts=skip_api)
                
        if os.path.exists(cta_audio_path):
            import shutil
            public_cta_name = f"{slug}-cta.wav"
            public_cta_path = os.path.join(remotion_public_dir, public_cta_name)
            shutil.copy(cta_audio_path, public_cta_path)
            
            script_data["cta_audio_file"] = f"faceless_assets/{public_cta_name}"
            frames, pages = process_audio_for_scene(cta_audio_path, fps=30)
            script_data["ctaDurationInFrames"] = frames
            script_data["ctaCaptionPages"] = pages
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
    
    # --- Phase F4: Final Render ---
    print("\n🎥 Phase F4: Rendering Final Video with Remotion")
    final_video_path = os.path.join(output_dir, "final_video.mp4")
    
    # We must run Remotion from its directory
    remotion_dir = os.path.abspath("remotion-editor")
    
    cmd = [
        "npx.cmd", "remotion", "render",
        "src/index.ts", "FacelessVideo",
        final_video_path,
        f"--props={script_path}",
        "--codec=h264",
        "--crf=18",
        "--pixel-format=yuv420p"
    ]
    
    import subprocess
    print("🎬 Running Remotion process. This might take a few minutes...")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=remotion_dir,
        shell=False # Safe execution, bypasses Windows shell quoting bugs
    )
    
    if result.returncode != 0:
        print(f"❌ Remotion render failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    else:
        print(f"🎉 SUCCESS! Final video rendered at: {final_video_path}")

    return output_dir

if __name__ == "__main__":
    # Test script if run directly
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "The psychology of optical illusions"
    # To test without consuming API credits:
    faceless_pipeline(topic, duration=20, template="tech", color_palette="cyberpunk", font_preset="roboto", skip_api=True)
