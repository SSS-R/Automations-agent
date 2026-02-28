import os
from dotenv import load_dotenv
from app.services.faceless.pipeline import faceless_pipeline

def main():
    load_dotenv()
    print("STARTING PIPELINE...")
    
    # Run the pipeline with the parameters we've been using
    result = faceless_pipeline(
        topic='The Japanese urban legend of the slit-mouthed woman',
        tone='dark mysterious',
        duration=45,
        template='minimal',
        audience='Gen Z horror lovers',
        goal='maximize retention and rewatches',
        hook_style='curiosity gap',
        skip_api=True
    )
    
    print(f"\nOUTPUT DIR: {result}")

if __name__ == "__main__":
    main()
