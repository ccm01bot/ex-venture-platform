from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from openai import AsyncOpenAI
from app.core.config import settings

router = APIRouter(prefix="/api/images", tags=["images"])


class ImageGenRequest(BaseModel):
    prompt: str
    style: str = "vivid"  # vivid or natural
    size: str = "1024x1024"  # 1024x1024, 1792x1024, 1024x1792
    quality: str = "standard"  # standard or hd


class ImageGenResponse(BaseModel):
    url: str
    revised_prompt: str
    error: Optional[str] = None


# Curated style presets users can pick from
STYLE_PRESETS = {
    "photorealistic": "Ultra-photorealistic, 8K, cinematic lighting, shallow depth of field, shot on Sony A7R IV",
    "digital_art": "High-quality digital art, vibrant colors, detailed illustration, trending on ArtStation",
    "3d_render": "Professional 3D render, octane render, volumetric lighting, high detail, studio quality",
    "watercolor": "Beautiful watercolor painting, soft washes, artistic brushstrokes, fine art quality",
    "minimalist": "Clean minimalist design, flat illustration, modern graphic design, simple shapes, limited color palette",
    "cinematic": "Cinematic film still, anamorphic lens, dramatic lighting, movie scene, 35mm film grain",
    "anime": "High-quality anime art, Studio Ghibli style, detailed, vibrant, professional illustration",
    "logo": "Professional logo design, vector style, clean lines, scalable, modern branding, white background",
    "thumbnail": (
        "YouTube thumbnail, 16:9. Dark solid background. Confident bearded man in dark t-shirt, "
        "intense eye contact, dramatic studio lighting. Massive bold yellow Impact-style text with "
        "heavy black drop shadow. Red arrow. Alex Hormozi / GaryVee style. Extremely high contrast."
    ),
    "hero_image": (
        "Photorealistic editorial photograph. Sleek modern desk near floor-to-ceiling window. "
        "Silver laptop with glowing cyan HUD on screen. Floating translucent holographic wireframe "
        "globe and data nodes in cyan/green glow. Warm golden hour sunlight, heavy bokeh, lens flares. "
        "Muted palette with cyan/green pops. Shallow depth of field."
    ),
}


@router.get("/presets")
async def get_presets():
    """Return available style presets."""
    return {
        "presets": [
            {"id": k, "name": k.replace("_", " ").title(), "description": v[:80] + "..."}
            for k, v in STYLE_PRESETS.items()
        ]
    }


@router.post("/generate", response_model=ImageGenResponse)
async def generate_image(req: ImageGenRequest):
    from app.core.gemini_images import generate_image_gemini

    has_gemini = settings.gemini_api_key and "your-" not in settings.gemini_api_key

    if not has_gemini:
        import urllib.parse
        import uuid
        seed = uuid.uuid4().hex[:8]
        encoded = urllib.parse.quote(req.prompt)
        return ImageGenResponse(
            url=f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={seed}",
            revised_prompt="Demo mode — Using Pollinations AI.",
            error="No Gemini API key configured. Add GEMINI_API_KEY to your .env file."
        )

    # Build the final prompt
    final_prompt = req.prompt
    for preset_id, preset_text in STYLE_PRESETS.items():
        if preset_id in req.prompt.lower():
            clean = req.prompt.lower().replace(preset_id, "").strip()
            final_prompt = f"{preset_text}. Subject: {clean}" if clean else preset_text
            break

    # Map size to Gemini aspect ratio
    size_to_aspect = {
        "1024x1024": "1:1",
        "1792x1024": "16:9",
        "1024x1792": "9:16",
    }
    aspect_ratio = size_to_aspect.get(req.size, "1:1")

    try:
        result = await generate_image_gemini(final_prompt, aspect_ratio=aspect_ratio)
        if result:
            return ImageGenResponse(
                url=result,
                revised_prompt=final_prompt,
            )
        else:
            import urllib.parse
            import uuid
            seed = uuid.uuid4().hex[:8]
            encoded = urllib.parse.quote(final_prompt)
            return ImageGenResponse(
                url=f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={seed}",
                revised_prompt=final_prompt,
                error="Google API returned empty parts. Fell back to Pollinations.",
            )
    except Exception as e:
        import urllib.parse
        import uuid
        seed = uuid.uuid4().hex[:8]
        encoded = urllib.parse.quote(final_prompt)
        return ImageGenResponse(
            url=f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={seed}",
            revised_prompt=final_prompt,
            error=str(e),
        )

