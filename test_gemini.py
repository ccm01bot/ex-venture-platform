import os
import asyncio
from google import genai
from google.genai import types

async def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No API KEY")
        return
        
    client = genai.Client(api_key=api_key)
    
    print("Testing generate_images with imagen-3.0-generate-002...")
    try:
        result = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt='A futuristic city in the desert',
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9"
            )
        )
        print("SUCCESS imagen:", result)
    except Exception as e:
        print("ERROR imagen:", str(e))

    print("Testing generate_content with gemini-2.5-flash-image...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Generate an image of a red dog",
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )
        print("SUCCESS gemini-2.5-flash:", response)
    except Exception as e:
        print("ERROR gemini-2.5-flash:", str(e))

if __name__ == "__main__":
    asyncio.run(main())
