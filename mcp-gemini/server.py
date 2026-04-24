import os
import io
import base64
import time
from typing import Optional

from mcp.server.fastmcp import FastMCP
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Initialize FastMCP Server
mcp = FastMCP("GeminiImageGen")

# Set the correct model available on free tier for image generation
_IMAGE_MODEL = "gemini-2.5-flash-image"

def _get_gemini_client():
    """Create a Gemini client using the API key from environment."""
    # Ensure GEMINI_API_KEY is available in the environment
    api_key = os.getenv("GEMINI_API_KEY") or "AIzaSyC--XfRUQTRRkXNZcZTRE_1MNUXjETZGMo"
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
    # For Gemini 2.5 Flash Image, we need to use v1beta
    return genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})

@mcp.tool()
def generate_image(prompt: str, output_path: Optional[str] = None) -> str:
    """
    Generate an image using Google Gemini (gemini-2.5-flash-image).
    
    Args:
        prompt: The description of the image to generate. Ensure no text/words are requested if unsupported.
        output_path: Optional absolute file path to save the generated image (e.g. /path/to/image.png).
                     If not provided, the image is saved to a default directory and its path is returned.
                     
    Returns:
        The absolute path to the generated image.
    """
    client = _get_gemini_client()
    
    # Retry up to 3 times with backoff for rate limits
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=_IMAGE_MODEL,
                contents=f"Generate an image with NO text, NO words, NO letters overlaid. Pure visual art only. {prompt}",
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )

            if (
                response.candidates
                and response.candidates[0].content
                and response.candidates[0].content.parts
            ):
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        img_bytes = part.inline_data.data
                        mime = part.inline_data.mime_type or "image/png"
                        ext = "png" if "png" in mime else "jpg"
                        
                        # Determine where to save
                        if not output_path:
                            # Save to assets directory relative to parent backend folder if possible, else current dir
                            default_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_images")
                            os.makedirs(default_dir, exist_ok=True)
                            filename = f"gemini_img_{int(time.time())}.{ext}"
                            output_path = os.path.join(default_dir, filename)
                            
                        with open(output_path, "wb") as f:
                            f.write(img_bytes)
                            
                        return f"Success! Image saved to: {output_path}"

            return "Error: Gemini returned no image parts."

        except Exception as exc:
            err_str = str(exc)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                wait = (attempt + 1) * 10 
                # Backoff
                time.sleep(wait)
                continue
            else:
                return f"Error: Gemini image generation failed: {exc}"

    return "Error: Gemini image generation exhausted all retries (likely rate limited)."

if __name__ == "__main__":
    mcp.run()
