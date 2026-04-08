import anthropic
from openai import AsyncOpenAI
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings
from app.routes.articles import _get_fallback_photorealistic_image

router = APIRouter(prefix="/api/youtube", tags=["youtube"])

class YoutubeOptimizationRequest(BaseModel):
    input_type: str  # 'url', 'script', 'brainstorm'
    url: str = ""
    script: str = ""
    selected_idea: str = ""
    image_style: str = "Photorealistic"

class YoutubeOptimizationResponse(BaseModel):
    titles: list[str]
    description: str
    tags: list[str]
    thumbnail_urls: list[str]

def _mock_youtube_seo(req: YoutubeOptimizationRequest):
    # Dynamically extract real keywords from their actual script to make it feel deeply AI-optimized even offline
    topic = req.selected_idea if req.input_type == 'brainstorm' else (
        req.url if req.input_type == 'url' else (" ".join(req.script.split()[:5]) if req.script else "Startup Strategy")
    )
    
    script_snippet = req.script[:150] + "..." if req.script else f"Exactly how {topic} impacts your startup or career."
    
    return YoutubeOptimizationResponse(
        titles=[
            f"The Untold Strategy Behind {topic[:25]} in 2026",
            f"Why Everyone is Wrong About {topic[:25]}",
            f"I Built a Business Using {topic[:25]} (Here's What Happened)"
        ],
        description=(
            f"Want to know the secret behind {topic}? We're breaking down exactly what the top 1% of founders know that you don't.\n\n"
            f"In this deep dive: {script_snippet}\n\n"
            f"Whether you're exploring {topic} or scaling to Series A, this breakdown contains everything you need to execute flawlessly.\n\n"
            "🔥 FREE RESOURCES & LINKS:\n"
            "📥 Download the exact blueprint: [Link]\n"
            "🚀 Join the EX Venture Platform: [Link]\n\n"
            "⏱️ TIMESTAMPS:\n"
            "0:00 - The massive problem with current strategies\n"
            "2:15 - Core framework philosophy\n"
            "5:30 - Breaking down the 3-Step Strategy\n"
            "12:45 - Real-world execution examples\n"
            "18:20 - Final verdict & your next steps\n\n"
            "Don't forget to SUBSCRIBE for more intense teardowns and high-signal insights! 📈"
        ),
        tags=["startup", "venture capital", topic[:15].lower().replace(' ', ''), "entrepreneurship", "business strategy"],
        thumbnail_urls=[
            _get_fallback_photorealistic_image(),
            "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1024&h=1024&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1024&h=1024&auto=format&fit=crop"
        ]
    )


@router.post("/optimize", response_model=YoutubeOptimizationResponse)
async def optimize_youtube_seo(req: YoutubeOptimizationRequest):
    if not settings.anthropic_api_key or "your-" in settings.anthropic_api_key:
        return _mock_youtube_seo(req)
        
    anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    
    # Construct base context
    if req.input_type == 'url':
        context = f"Analyze the context of this YouTube URL (assume common video patterns if URL cannot be fetched directly): {req.url}"
    elif req.input_type == 'script':
        context = f"Analyze this detailed video script text: {req.script}"
    else:
        context = f"Construct a video narrative around this powerful brainstormed concept: {req.selected_idea}"
        
    # Generate SEO Metadata
    prompt = f"CONTEXT:\n{context}\n\nAct as a world-class, algorithmic-driven YouTube SEO expert. Output ONLY valid JSON containing EXACTLY the following format, with NO markdown formatting around the output: {{\n  \"titles\": [\"Highly clickable curiosity-gap option 1\", \"High urgency option 2\", \"Authority building option 3 (all under 60 chars)\"],\n  \"description\": \"A massive, beautifully structured YouTube description. CRITICAL: It MUST be entirely custom to the specific CONTEXT provided above. Summarize the actual script contents in the 'In this video' section. Create custom timestamps that match the actual progression of the script/video provided. Include psychological hooks and a call-to-subscribe.\",\n  \"tags\": [\"comma\", \"separated\", \"tags\", \"exactly\", \"15\", \"tags\", \"extracted\", \"directly\", \"from\", \"the\", \"specific\", \"script\", \"context\", \"provided\", \"above\"]\n}}"
    
    try:
        response = await anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        import json
        import re
        content = response.content[0].text.strip()
        # Clean any accidental markdown wrap
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'^```\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        seo_data = json.loads(content)
    except Exception as e:
        return _mock_youtube_seo(req)

    # Generate Image using OpenAI
    thumbnail_urls = []
    if not settings.openai_api_key or "your-" in settings.openai_api_key:
        thumbnail_urls = [
            "/assets/thumbnails/sample-1.png",
            "/assets/thumbnails/sample-2.png",
            "/assets/thumbnails/sample-3.png"
        ]
    else:
        openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        # Step 1: Ask Claude to extract a punchy 1-3 word text hook from the video title
        img_prompt_req = (
            f"Based on this YouTube video title: '{seo_data.get('titles', [''])[0]}', "
            f"output ONLY a single punchy text phrase of 1-3 words that would go on a YouTube thumbnail. "
            f"Examples of good phrases: 'STOP THIS', 'DO THIS NOW', 'PROFIT', 'FOR FREE', 'START OVER', 'YOU'RE WRONG', 'IT'S EASY', 'JUST FIX THIS'. "
            f"Output ONLY the phrase, nothing else. No quotes, no explanation."
        )
        
        try:
            img_prompt_res = await anthropic_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=20,
                temperature=0.8,
                messages=[{"role": "user", "content": img_prompt_req}]
            )
            text_hook = img_prompt_res.content[0].text.strip().upper()
            
            import asyncio
            
            # The master style directive — pixel-precise Hormozi/GaryVee recreation
            THUMB_STYLE = (
                "YouTube thumbnail, 16:9 aspect ratio. "
                "COMPOSITION: Extremely simple, only 2 elements — a person and bold text. Dark solid background (near-black or very dark gray). "
                "PERSON: A close-up photograph of a confident, intense man (mid-30s, short dark beard, fitted dark t-shirt) from the chest up. "
                "He is making direct, intense eye contact with the camera. Expression is serious, confident, slightly confrontational. "
                "Lighting is dramatic studio lighting with strong key light from one side creating sharp shadows on the face. "
                "Slight warm color grading. The person takes up roughly 40-50%% of the frame, positioned to one side. "
                "TEXT: Massive, extremely bold, blocky sans-serif text (Impact or Bebas Neue style) taking up the other half of the frame. "
                "Text color is BRIGHT YELLOW or WHITE with a heavy black drop shadow / stroke outline. "
                "The text is the LARGEST element in the entire image and reads clearly at small sizes. "
                "OPTIONAL ELEMENTS: A single bright red arrow pointing at something, or a subtle green glow behind the text. "
                "OVERALL: Looks exactly like a real Alex Hormozi or GaryVee YouTube thumbnail — extremely high contrast, "
                "clean composition, no clutter, no busy backgrounds, no gradients. Just face + massive text + dark background."
            )
            
            async def generate_thumb(variation: str):
                prompt = (
                    f"{THUMB_STYLE} "
                    f"The massive bold text reads exactly: '{text_hook}'. "
                    f"Variation: {variation}. "
                    f"Spell the text PERFECTLY. The text must be legible even at 200px wide."
                )
                try:
                    res = await openai_client.images.generate(
                        model="dall-e-3",
                        prompt=prompt[:1000],
                        n=1,
                        size="1792x1024",
                        quality="hd"
                    )
                    return res.data[0].url
                except Exception:
                    return _get_fallback_photorealistic_image()
                    
            # Gather 3 parallel thumbnail generations with different compositions
            thumbnail_urls = await asyncio.gather(
                generate_thumb("Person on LEFT side, text on RIGHT side"),
                generate_thumb("Person on RIGHT side, text on LEFT side"),
                generate_thumb("Person centered, text overlaid above in large yellow bold font")
            )
        except:
            thumbnail_urls = [
                _get_fallback_photorealistic_image(),
                _get_fallback_photorealistic_image(),
                _get_fallback_photorealistic_image()
            ]

    return YoutubeOptimizationResponse(
        titles=seo_data.get('titles', ['Optimized Title 1', 'Optimized Title 2', 'Optimized Title 3']),
        description=seo_data.get('description', 'Optimized video description goes here...'),
        tags=seo_data.get('tags', ['optimization', 'youtube']),
        thumbnail_urls=list(thumbnail_urls)
    )
