import os
from dotenv import load_dotenv
from app.services.faceless.pipeline import faceless_pipeline

def main():
    load_dotenv()
    print("STARTING PIPELINE...")
    
    # Run the pipeline with the user's specified parameters
    result = faceless_pipeline(
        topic='A newly released AI tool that could change how developers work',
        tone='smart futuristic slightly intense',
        duration=30,
        template='tech',
        audience='tech savvy Gen Z, developers, startup founders',
        goal='maximize retention and authority positioning',
        hook_style='shock + curiosity gap',
        skip_api=False
    )
    
    print(f"\nOUTPUT DIR: {result}")

if __name__ == "__main__":
    main()
