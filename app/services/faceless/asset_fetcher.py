import os
import requests
from typing import Optional

def get_pexels_api_key() -> str:
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        raise ValueError("PEXELS_API_KEY environment variable not set. Please get one from https://www.pexels.com/api/")
    return api_key

def download_video(url: str, filepath: str) -> None:
    """Download a video file from a given URL."""
    print(f"Downloading video to {filepath}...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024*1024):
                f.write(chunk)
        print(f"✅ Successfully downloaded {filepath}")
    else:
        raise Exception(f"Failed to download video: HTTP {response.status_code}")

def fetch_stock_video(keyword: str, output_path: str) -> str:
    """
    Searches Pexels for a 9:16 vertical video matching the keyword.
    Downloads it to output_path.
    Returns the absolute path to the downloaded file.
    """
    api_key = get_pexels_api_key()
    headers = {
        "Authorization": api_key
    }
    
    # Orientation 'portrait' means 9:16 or similar vertical format.
    # We want videos around 15-30s ideally for a scene, but Pexels might just give anything.
    url = f"https://api.pexels.com/videos/search?query={keyword}&orientation=portrait&per_page=5"
    
    print(f"Searching Pexels for: '{keyword}' (vertical)...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Pexels API error: {response.text}")
        
    data = response.json()
    videos = data.get("videos", [])
    
    if not videos:
        print(f"⚠️ No Pexels video found for '{keyword}', looking for fallback image instead...")
        # Optional: Implement a fallback to Pixelbay or returning an empty string to use Remotion's gradient background.
        return ""
        
    # Pick the first video
    video = videos[0]
    video_files = video.get("video_files", [])
    
    # Try to find a good quality hd file, preferably 1080x1920 (or closest)
    selected_file = None
    for vf in video_files:
        if vf.get("quality") == "hd" and vf.get("width") == 1080 and vf.get("height") == 1920:
            selected_file = vf
            break
            
    # If perfect match not found, fallback to any HD vertical, or just the best available
    if not selected_file:
        for vf in video_files:
            if vf.get("quality") in ["hd", "sd"]:
                selected_file = vf
                if vf.get("width", 0) < vf.get("height", 0):
                    break
    
    if not selected_file and video_files:
        selected_file = video_files[0]
        
    if not selected_file:
        return ""
        
    video_link = selected_file.get("link")
    
    # Simple caching based on video ID
    video_id = video.get("id")
    cache_dir = os.path.abspath("temp/cache/pexels")
    os.makedirs(cache_dir, exist_ok=True)
    
    cached_path = os.path.join(cache_dir, f"{video_id}.mp4")
    abs_path = os.path.abspath(output_path)
    
    if os.path.exists(cached_path):
        print(f"♻️  Using cached Pexels video {video_id}")
        import shutil
        shutil.copy(cached_path, abs_path)
    else:
        # Download and save to cache, then copy
        download_video(video_link, cached_path)
        import shutil
        shutil.copy(cached_path, abs_path)
    
    return abs_path
