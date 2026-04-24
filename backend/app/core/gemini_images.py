"""Shared Gemini image generation utility used by all dashboard modules."""
import asyncio
import base64
import logging
import time

from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

# Use the v1beta API for image generation models
_IMAGE_MODEL = "gemini-2.5-flash-image"


def _get_gemini_client():
    """Create a Gemini client using the API key from settings."""
    api_key = settings.gemini_api_key
    if not api_key or "your-" in api_key:
        return None
    # Force 'v1' to ensure imagen-3.0 is recognized
    return genai.Client(api_key=api_key, http_options={"api_version": "v1"})


def _generate_image_sync(prompt: str, aspect_ratio: str = "16:9") -> str | None:
    """
    Synchronous image generation using Gemini's dedicated Imagen 3 model.
    Returns a data URI or None on failure.
    """
    client = _get_gemini_client()
    if not client:
        logger.warning("No Gemini API key configured")
        return None

    # Retry up to 3 times with backoff for rate limits
    for attempt in range(3):
        try:
            # Map standard aspect ratios to Imagen aspect ratios
            valid_ratio = "16:9" 
            if aspect_ratio in ["1:1", "16:9", "9:16", "3:4", "4:3"]:
                valid_ratio = aspect_ratio
                
            result = client.models.generate_images(
                model='imagen-3.0-generate-002',
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=valid_ratio,
                    output_mime_type="image/jpeg"
                )
            )

            if result and result.generated_images and len(result.generated_images) > 0:
                img_bytes = result.generated_images[0].image.image_bytes
                if img_bytes:
                    mime = "image/jpeg"
                    b64 = base64.b64encode(img_bytes).decode("utf-8")
                    logger.info("Imagen image generated successfully (%d bytes)", len(img_bytes))
                    return f"data:{mime};base64,{b64}"

            logger.warning("Imagen returned no image parts")
            return None

        except Exception as exc:
            err_str = str(exc)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                wait = (attempt + 1) * 10  # 10s, 20s, 30s
                logger.warning("Gemini rate limited, retrying in %ds (attempt %d/3)", wait, attempt + 1)
                time.sleep(wait)
                continue
            else:
                logger.error("Gemini image generation failed: %s", exc)
                return None

    logger.error("Gemini image generation exhausted all retries")
    return None


async def generate_image_gemini(
    prompt: str,
    aspect_ratio: str = "16:9",
) -> str | None:
    """
    Async wrapper — generates an image using Gemini's native image generation.
    Returns a data URI (base64-encoded image) or None on failure.
    """
    return await asyncio.to_thread(_generate_image_sync, prompt, aspect_ratio)
