import asyncio
from google import genai
from google.genai import types
from app.core.config import settings

async def main():
    api_key = settings.gemini_api_key
    print(f"Key loaded: {bool(api_key)}")
    client = genai.Client(api_key=api_key, http_options={"api_version": "v1"})
    
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
        print("SUCCESS imagen:", type(result), dir(result))
        if hasattr(result, "generated_images"):
            print("Generated images array length:", len(result.generated_images))
    except Exception as e:
        print("ERROR imagen:", str(e))

if __name__ == "__main__":
    asyncio.run(main())
