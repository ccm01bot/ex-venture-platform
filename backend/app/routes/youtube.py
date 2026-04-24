import asyncio
import json
import logging
import re

import anthropic
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.core.gemini_images import generate_image_gemini
from app.routes.articles import _get_fallback_photorealistic_image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/youtube", tags=["youtube"])


class YoutubeOptimizationRequest(BaseModel):
    input_type: str  # 'url', 'script', 'brainstorm'
    url: str = ""
    script: str = ""
    selected_idea: str = ""
    image_style: str = "Photorealistic"
    image_quality: str = "draft"

class ThumbnailOnlyRequest(BaseModel):
    title: str
    image_style: str = "Photorealistic"
    image_quality: str = "draft"

@router.post("/thumbnail")
async def generate_single_thumbnail(req: ThumbnailOnlyRequest):
    """Generates just one thumbnail variation without re-running SEO text logic."""
    has_gemini = settings.gemini_api_key and "your-" not in settings.gemini_api_key
    style_directive = STYLE_DIRECTIVES.get(req.image_style, STYLE_DIRECTIVES["Photorealistic"])
    
    is_draft = req.image_quality == "draft"
    
    import uuid
    variance_seed = uuid.uuid4().hex[:8]
    
    if is_draft:
        import urllib.parse
        pollinations_prompt = f"{style_directive} {req.title}"
        encoded = urllib.parse.quote(pollinations_prompt)
        return {"url": f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true&seed={variance_seed}"}
    
    if not has_gemini:
        return {"url": _get_fallback_photorealistic_image()}
        
    concept = {"visual_concept": req.title}
    prompt = _build_thumbnail_prompt(style_directive, concept, req.title)
    from app.core.gemini_images import generate_image_gemini
    result = await generate_image_gemini(prompt, aspect_ratio="16:9")
    return {"url": result or _get_fallback_photorealistic_image()}

class BrainstormResponse(BaseModel):
    ideas: list[str]


class YoutubeOptimizationResponse(BaseModel):
    titles: list[str]
    description: str
    tags: list[str]
    thumbnail_urls: list[str]


# Each frontend style maps to concrete visual directives that get injected
# into the image prompt. Keys must stay in sync with frontend/app/youtube-seo/page.tsx STYLES.
STYLE_DIRECTIVES: dict[str, str] = {
    "Photorealistic": (
        "Hyper-realistic studio photograph. Sharp focus, shallow depth of field, "
        "dramatic key light from one side casting hard shadows, slight warm grade. "
        "Looks like a DSLR shot, not AI."
    ),
    "Illustration": (
        "Bold modern digital illustration, thick clean linework, vibrant flat colors with subtle gradients, "
        "graphic-novel energy, slight halftone texture."
    ),
    "Minimalist": (
        "Ultra-minimalist composition. One subject, massive negative space, two-color palette, "
        "no clutter, no gradients, Swiss design influence."
    ),
    "3D Render": (
        "Polished 3D render in the style of modern Octane/Blender hero shots, soft global illumination, "
        "glossy materials, subtle subsurface scattering, studio HDRI lighting."
    ),
    "Watercolor": (
        "Loose watercolor painting, visible paper texture, soft pigment bleeds, hand-painted brush strokes, "
        "muted-but-warm palette, white margins."
    ),
    "Flat Design": (
        "Flat vector design, geometric shapes, no shadows or gradients, bold primary colors, "
        "Material Design influence, clean and corporate."
    ),
    "Cinematic": (
        "Cinematic film still, anamorphic widescreen feel, moody teal-and-orange color grade, "
        "atmospheric haze, dramatic rim lighting, Hollywood blockbuster aesthetic."
    ),
    "Abstract": (
        "Bold abstract composition, expressive color blocking, unexpected geometric forms, "
        "high-contrast palette, gallery-art energy."
    ),
    "Isometric": (
        "Isometric 3D scene, 30-degree angle, miniature diorama feel, soft pastel palette, "
        "tiny stylized props arranged around the subject."
    ),
    "Editorial": (
        "Editorial magazine cover photography, refined typography negative space, sophisticated color grade, "
        "Vogue / WIRED cover energy, premium feel."
    ),
}

DEFAULT_STYLE_DIRECTIVE = STYLE_DIRECTIVES["Photorealistic"]


def _extract_hook(title: str) -> str:
    """Extract a punchy 1-3 word ALL-CAPS hook from a title for thumbnail text overlay."""
    # Look for strong hook words/phrases in the title
    title_lower = title.lower()
    hooks = [
        ("wrong", "YOU'RE WRONG"), ("fail", "DON'T DO THIS"), ("secret", "THE SECRET"),
        ("truth", "THE TRUTH"), ("stop", "STOP THIS"), ("never", "NEVER DO THIS"),
        ("mistake", "BIG MISTAKE"), ("how to", "DO THIS NOW"), ("why", "HERE'S WHY"),
        ("guide", "FULL GUIDE"), ("complete", "WATCH THIS"), ("built", "I DID IT"),
        ("million", "MILLIONS"), ("free", "FOR FREE"), ("hack", "LIFE HACK"),
        ("change", "GAME CHANGER"), ("habit", "DO THIS DAILY"), ("best", "THE BEST"),
        ("worst", "AVOID THIS"), ("strategy", "THE STRATEGY"), ("untold", "EXPOSED"),
    ]
    for keyword, hook in hooks:
        if keyword in title_lower:
            return hook
    # Default: take first 2-3 impactful words
    words = [w for w in title.split() if len(w) > 3 and w.lower() not in ("this", "that", "with", "from", "about", "behind")]
    return " ".join(words[:2]).upper() if words else "WATCH THIS"


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

@router.post("/brainstorm", response_model=BrainstormResponse)
async def brainstorm_concepts():
    import random
    has_anthropic = settings.anthropic_api_key and "your-" not in settings.anthropic_api_key
    
    # Force extreme randomness by injecting topics/styles
    themes = ["Venture Capital", "AI Engineering", "B2B SaaS Growth", "Solo Founder Survival", "Tech Industry Crises", "Bootstrapping"]
    angles = ["A harsh truth", "A mathematical breakdown", "A hidden secret", "A complete step-by-step guide", "A crazy experiment"]
    random.shuffle(themes)
    random.shuffle(angles)

    if has_anthropic:
        anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        prompt = (
            f"Generate 4 highly viral, completely unique YouTube video concepts related to Tech and Business.\n"
            f"Themes to inspire you right now: {themes[:3]}.\n"
            f"Angles to use: {angles[:3]}.\n"
            "Format the output strictly as a JSON array of 4 strings. No markdown formatting, just the raw list. Make them sound like 10M view viral hits."
        )
        try:
            response = await anthropic_client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=1000,
                temperature=0.99,
                messages=[{"role": "user", "content": prompt}],
            )
            data_str = response.content[0].text.strip()
            data_str = re.sub(r'^```json\s*', '', data_str)
            data_str = re.sub(r'^```\s*', '', data_str)
            data_str = re.sub(r'\s*```$', '', data_str)
            ideas = json.loads(data_str)
            if isinstance(ideas, list) and len(ideas) >= 4:
                return BrainstormResponse(ideas=ideas[:4])
        except Exception as exc:
            logger.warning(f"Brainstorm failed: {exc}")

    # Fallback if no Anthropic key or if it failed
    return BrainstormResponse(ideas=[
        f"Why {themes[0]} is Broken in 2026 ({angles[0]})",
        f"The {themes[1]} Matrix: How I Made Millions",
        f"Stop Doing {themes[2]} Like This",
        f"A Complete Guide to 100x Your {themes[3]}"
    ])



def _build_seo_prompt(context: str) -> str:
    """Single Claude call that returns SEO metadata AND 3 distinct thumbnail concepts."""
    return (
        f"CONTEXT:\n{context}\n\n"
        "Act as a world-class YouTube SEO expert AND a thumbnail art director. "
        "Output ONLY valid JSON (no markdown fences) with EXACTLY this shape:\n"
        "{\n"
        '  "titles": ["clickable curiosity-gap option (<60 chars)", "high-urgency option (<60 chars)", "authority option (<60 chars)"],\n'
        '  "description": "A massive, beautifully structured YouTube description CUSTOM to the CONTEXT above. Summarize actual script contents in an \'In this video\' section. Include custom timestamps that reflect the real progression of the video. Add psychological hooks and a call-to-subscribe.",\n'
        '  "tags": ["exactly", "15", "tags", "extracted", "from", "the", "specific", "context", "above", "no", "generic", "filler", "words", "high", "intent"],\n'
        '  "thumbnails": [\n'
        '    {\n'
        '      "text_hook": "1-3 word ALL-CAPS shock phrase (e.g. STOP THIS, ITS OVER, DO THIS NOW)",\n'
        '      "visual_concept": "A vivid, specific scene description for a DRAMATIC/DARK thumbnail. Think: moody lighting, intense expression, dark background with a single bold color pop. Describe the exact subject, their pose/expression, and the atmosphere.",\n'
        '      "color_scheme": "dominant color + accent (e.g. deep black background with neon red accents)",\n'
        '      "mood": "dramatic"\n'
        '    },\n'
        '    {\n'
        '      "text_hook": "1-3 word ALL-CAPS hype phrase (e.g. GAME CHANGER, FOR FREE, JUST DO IT)",\n'
        '      "visual_concept": "A vivid, specific scene description for a BOLD/ENERGETIC thumbnail. Think: bright saturated colors, dynamic angle, explosive energy, split backgrounds. Describe the exact subject, action, and visual energy.",\n'
        '      "color_scheme": "dominant color + accent (e.g. electric blue split with hot orange)",\n'
        '      "mood": "energetic"\n'
        '    },\n'
        '    {\n'
        '      "text_hook": "1-3 word ALL-CAPS authority phrase (e.g. THE TRUTH, EXPOSED, LEARN THIS)",\n'
        '      "visual_concept": "A vivid, specific scene description for a CLEAN/AUTHORITY thumbnail. Think: professional, minimal, white or light background, clean composition, trust-building. Describe the exact subject and the premium, polished feel.",\n'
        '      "color_scheme": "dominant color + accent (e.g. clean white with navy blue and gold)",\n'
        '      "mood": "authoritative"\n'
        '    }\n'
        '  ]\n'
        "}\n\n"
        "ABSOLUTE RULE FOR VARIANCE: The 3 titles must be entirely different angles (e.g. one fear-based, one curiosity-based, one authority-based). "
        "The 3 thumbnail concepts MUST BE RADICALLY DIFFERENT from each other. They cannot use the same subjects, the same backgrounds, or the same metaphors. "
        "Variation 1: Close-up human emotion/face. Variation 2: Abstract/symbolic object (no faces). Variation 3: Wide cinematic scene. "
        "FORCE extreme visual diversity. If they look even marginally similar, you have failed."
    )


def _parse_seo_json(raw: str) -> dict:
    content = raw.strip()
    content = re.sub(r'^```json\s*', '', content)
    content = re.sub(r'^```\s*', '', content)
    content = re.sub(r'\s*```$', '', content)
    return json.loads(content)


# Each thumbnail variant gets its own unique mood-based composition rules
THUMBNAIL_MOODS = {
    "dramatic": (
        "Dark, moody composition. Subject fills 60% of the frame on the left, intense close-up. "
        "Background is near-black with a single dramatic color splash or light beam. "
        "Cinematic lighting: harsh side light, deep shadows. Text on the right side, stacked vertically."
    ),
    "energetic": (
        "Explosive, high-energy composition. Dynamic diagonal split background with two contrasting bold colors. "
        "Subject in an action pose or gesturing excitedly, positioned on the right. "
        "Visual elements: arrows, speed lines, glowing effects. Text dominates the left, angled slightly for urgency."
    ),
    "authoritative": (
        "Clean, premium composition. Soft, professional background (gradient or bokeh). "
        "Subject centered with confident, calm expression and professional pose. "
        "Minimal visual clutter. Text at the top or bottom, clean and large. Feels like a TED Talk or Bloomberg cover."
    ),
}


def _build_thumbnail_prompt(
    style_directive: str,
    thumbnail_concept: dict,
    fallback_subject: str,
) -> str:
    mood = thumbnail_concept.get("mood", "dramatic")
    composition = THUMBNAIL_MOODS.get(mood, THUMBNAIL_MOODS["dramatic"])
    visual_concept = thumbnail_concept.get("visual_concept", fallback_subject)
    text_hook = (thumbnail_concept.get("text_hook") or "WATCH THIS").strip().upper()
    color_scheme = thumbnail_concept.get("color_scheme", "dark with bold accents")

    import time
    variance_seed = str(time.time_ns())[-6:]
    
    return (
        f"YouTube thumbnail, 16:9 aspect ratio. MAXIMIZE CTR.\n\n"
        f"ABSOLUTE DIRECTIVE: Make this visually UNIQUE compared to typical generations. Inject radical creative flair. [SEED: {variance_seed}]\n\n"
        f"VISUAL STYLE: {style_directive}\n\n"
        f"SCENE: {visual_concept}\n\n"
        f"COLOR PALETTE: {color_scheme}. STRICTLY adhere to this unique palette to ensure it looks different from others.\n\n"
        f"COMPOSITION & MOOD: {composition}\n\n"
        f"TEXT OVERLAY: Massive, extremely bold blocky sans-serif text reading EXACTLY: '{text_hook}'. "
        f"Text MUST contrast maximally against the background. Spell every letter perfectly.\n\n"
        f"RULES: No clutter. No watermarks. High contrast. Readable at tiny sizes. "
    )


@router.post("/optimize", response_model=YoutubeOptimizationResponse)
async def optimize_youtube_seo(req: YoutubeOptimizationRequest):
    # Extract the topic from whatever input the user gave
    topic = ""
    if req.input_type == 'brainstorm':
        topic = req.selected_idea or "Startup Strategy"
    elif req.input_type == 'url':
        topic = req.url or "YouTube Video Analysis"
    elif req.input_type == 'script':
        topic = " ".join(req.script.split()[:20]) if req.script else "Video Script"

    has_anthropic = settings.anthropic_api_key and "your-" not in settings.anthropic_api_key
    has_openai = settings.openai_api_key and "your-" not in settings.openai_api_key

    # ── STEP 1: Generate SEO metadata (Claude or mock) ──────────────
    if has_anthropic:
        anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        if req.input_type == 'url':
            context = f"Analyze the context of this YouTube URL (assume common video patterns if URL cannot be fetched directly): {req.url}"
        elif req.input_type == 'script':
            context = f"Analyze this detailed video script text: {req.script}"
        else:
            context = f"Construct a video narrative around this powerful brainstormed concept: {req.selected_idea}"

        try:
            response = await anthropic_client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=3000,
                temperature=0.8,
                messages=[{"role": "user", "content": _build_seo_prompt(context)}],
            )
            seo_data = _parse_seo_json(response.content[0].text)
        except Exception as exc:
            logger.warning("YouTube SEO Claude call failed, using mock SEO: %s", exc)
            seo_data = None
    else:
        seo_data = None

    # If Claude wasn't available or failed, generate mock SEO text
    if seo_data is None:
        script_snippet = req.script[:150] + "..." if req.script else f"Exactly how {topic} impacts your startup or career."
        seo_data = {
            "titles": [
                f"The Untold Strategy Behind {topic[:30]} in 2026",
                f"Why Everyone is Wrong About {topic[:30]}",
                f"I Built a Business Using {topic[:30]} (Here's What Happened)"
            ],
            "description": (
                f"Want to know the secret behind {topic}? We're breaking down exactly what the top 1% of founders know that you don't.\n\n"
                f"In this deep dive: {script_snippet}\n\n"
                f"Whether you're exploring {topic} or scaling to Series A, this breakdown contains everything you need to execute.\n\n"
                "🔥 FREE RESOURCES & LINKS:\n"
                "📥 Download the exact blueprint: [Link]\n"
                "🚀 Join the EX Venture Platform: [Link]\n\n"
                "⏱️ TIMESTAMPS:\n"
                "0:00 - The massive problem with current strategies\n"
                "2:15 - Core framework philosophy\n"
                "5:30 - Breaking down the 3-Step Strategy\n"
                "12:45 - Real-world execution examples\n"
                "18:20 - Final verdict & your next steps\n\n"
                "Don't forget to SUBSCRIBE for more insights! 📈"
            ),
            "tags": ["startup", "venture capital", topic[:15].lower().replace(' ', ''), "entrepreneurship", "business strategy",
                     "founder", "growth", topic[:10].lower(), "2026", "strategy", "success",
                     "how to", "guide", "tutorial", "expert"],
            "thumbnails": []  # Will be filled with topic-based concepts below
        }

    # ── STEP 2: Generate a unique thumbnail FOR EACH title variation ──
    titles = seo_data.get("titles", [
        f"The Untold Strategy Behind {topic[:25]}",
        f"Why Everyone is Wrong About {topic[:25]}",
        f"I Built a Business Using {topic[:25]}"
    ])

    # Use Claude-generated thumbnail concepts if available, otherwise build from titles
    claude_concepts = seo_data.get("thumbnails", [])
    style_directive = STYLE_DIRECTIVES.get(req.image_style, DEFAULT_STYLE_DIRECTIVE)

    # Build one thumbnail concept per title — each visually matches its title
    moods = ["dramatic", "energetic", "authoritative"]
    thumbnail_concepts = []
    for i, title in enumerate(titles[:3]):
        if i < len(claude_concepts):
            # Use Claude-generated concept but override hook with actual title
            concept = claude_concepts[i]
            concept["text_hook"] = _extract_hook(title)
            concept["visual_concept"] = concept.get("visual_concept", "") + f" The scene directly illustrates: '{title}'."
            thumbnail_concepts.append(concept)
        else:
            # Generate fallback concepts with massive forced differences
            mood = moods[i % len(moods)]
            subjects = [
                "A dramatic extreme close-up of a stressed or shocked person holding their head",
                "A glowing neon 3D conceptual object exploding or shattering in mid-air (no humans)",
                "A wide cinematic professional stage with a confident speaker and sleek charts"
            ]
            thumbnail_concepts.append({
                "text_hook": _extract_hook(title),
                "visual_concept": (
                    f"{subjects[i % 3]}. "
                    f"This must heavily conceptualize the title: '{title}' about {topic[:40]}. "
                    "Make it radically different from the other variations visually."
                ),
                "color_scheme": ["Deep charcoal black with blinding neon cyan accents", "Electric purple split down the middle with radioactive yellow", "Crisp arctic white with deep navy blue and metallic gold"][i % 3],
                "mood": mood,
            })

    fallback_subject = f"A surreal, highly conceptual visual metaphor for {topic[:50]}"

    # ── STEP 3: Generate unique thumbnails via Gemini Imagen ──────────
    has_gemini = settings.gemini_api_key and "your-" not in settings.gemini_api_key

    if has_gemini:
        # Execute sequentially instead of gather to strictly bypass Gemini's parallel caching layer
        # which can return duplicated images if requests ping the load balancer at the exact same millisecond.
        thumbnail_urls = []
        # Generate 1 image by default to reduce output token cost by 66%
        for index, concept in enumerate(thumbnail_concepts[:1]):
            import uuid
            variance_seed = uuid.uuid4().hex[:8]
            is_draft = getattr(req, "image_quality", "draft") == "draft"
            
            if is_draft:
                import urllib.parse
                clean_concept = concept["visual_concept"].split("[System")[0].strip()
                pollinations_prompt = f"{style_directive} {clean_concept} with text saying {concept.get('text_hook', '')}"
                encoded = urllib.parse.quote(pollinations_prompt)
                thumbnail_urls.append(f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true&seed={variance_seed}")
            else:
                # Premium Google Gemini generation
                concept["visual_concept"] += f" [System Enforcer ID: {index+1}]"
                prompt = _build_thumbnail_prompt(style_directive, concept, fallback_subject)
                try:
                    result = await generate_image_gemini(prompt, aspect_ratio="16:9")
                    if not result:
                        print("Gemini returned None, activating dynamic fallback...")
                        import urllib.parse
                        import uuid
                        variance_seed = uuid.uuid4().hex[:8]
                        pollinations_prompt = f"YouTube thumbnail {style_directive} {topic} cinematic lighting ultra detailed"
                        encoded = urllib.parse.quote(pollinations_prompt)
                        thumbnail_urls.append(f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true&seed={variance_seed}")
                    else:
                        thumbnail_urls.append(result)
                except Exception as e:
                    print(f"Gemini thumbnail generation exception: {str(e)}")
                    import urllib.parse
                    import uuid
                    variance_seed = uuid.uuid4().hex[:8]
                    pollinations_prompt = f"YouTube thumbnail {style_directive} {topic} cinematic lighting ultra detailed"
                    encoded = urllib.parse.quote(pollinations_prompt)
                    thumbnail_urls.append(f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true&seed={variance_seed}")
                # Brief pause to ensure Google assigns a wholly separate generation node
                await asyncio.sleep(1.5)

    else:
        thumbnail_urls = [
            _get_fallback_photorealistic_image(),
            _get_fallback_photorealistic_image(),
            _get_fallback_photorealistic_image(),
        ]

    return YoutubeOptimizationResponse(
        titles=titles[:3],
        description=seo_data.get('description', 'Optimized video description goes here...'),
        tags=seo_data.get('tags', ['optimization', 'youtube']),
        thumbnail_urls=thumbnail_urls,
    )

