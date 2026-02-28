import os
from dotenv import load_dotenv
load_dotenv()
import google.generativeai as genai
genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
print("API Key loaded:", bool(os.environ.get('GOOGLE_API_KEY')))
print("Supported models for generateContent:")
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(m.name)
