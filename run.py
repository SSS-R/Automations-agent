import sys
import os

# Add the parent directory to sys.path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.pipeline import orchestrate_pipeline

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run.py <video_url>")
        sys.exit(1)
        
    url = sys.argv[1]
    orchestrate_pipeline(url)
