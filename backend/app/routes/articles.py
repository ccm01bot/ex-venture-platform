import asyncio
import hashlib
import base64
import math
import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
import anthropic
from openai import AsyncOpenAI
from app.core.config import settings
import re

router = APIRouter(prefix="/api/articles", tags=["articles"])


class ArticleRequest(BaseModel):
    platform: str = "Article"
    topic: str = ""
    keywords: str = ""
    tone: str = "professional"
    length: str = "medium"
    video_url: str = ""
    image_style: str = "Photorealistic"
    image_quality: str = "draft"
    source_urls: Optional[List[str]] = None
    web_research: bool = False


class HeroImageRequest(BaseModel):
    topic: str
    image_style: str = "Photorealistic"
    image_quality: str = "draft"

@router.post("/hero-image")
async def generate_single_hero_image(req: HeroImageRequest):
    """Generates just one hero image without running the Anthropic article generation."""
    has_gemini = settings.gemini_api_key and "your-" not in settings.gemini_api_key
    style_directive = IMAGE_STYLE_MAP.get(req.image_style, IMAGE_STYLE_MAP["Photorealistic"])
    
    is_draft = req.image_quality == "draft"
    
    import uuid
    variance_seed = uuid.uuid4().hex[:8]
    
    if is_draft:
        import urllib.parse
        pollinations_prompt = f"{style_directive} {req.topic} editorial article hero image"
        encoded = urllib.parse.quote(pollinations_prompt)
        return {"url": f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true&seed={variance_seed}"}
    
    import random
    concrete_visuals = [
        "modern business executives analyzing structural data over a glass architectural table",
        "focused entrepreneur sketching architectural diagrams on a clean whiteboard",
        "bustling creative agency office scene infused with warm natural sunlight",
        "premium venture capital board meeting with dramatic professional lighting",
        "close-up portrait of a visionary leader looking thoughtfully through a skyscraper window",
        "sleek minimalist workspace with organic trailing plants and architectural blueprints",
        "innovative tech founders collaborating over documents in an industrial loft",
        "dynamic wide-angle shot of a premium corporate workspace bustling with professionals"
    ]
    enhanced_subject = f"{req.topic}. Visual Scene: {random.choice(concrete_visuals)}"

    if not has_gemini:
        import urllib.parse
        pollinations_prompt = f"{style_directive} {enhanced_subject} highly detailed editorial photography"
        encoded = urllib.parse.quote(pollinations_prompt)
        return {"url": f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true&seed={variance_seed}"}
        
    image_prompt = (
        f"ABSOLUTE DIRECTIVE: Make this visually UNIQUE compared to typical generations. "
        f"Inject radical creative flair. [SEED: {variance_seed}]\n\n"
        f"STYLE GUIDANCE: {style_directive}\n\n"
        f"SCENE TO REPRESENT: {enhanced_subject}."
    )
    from app.core.gemini_images import generate_image_gemini
    try:
        result = await generate_image_gemini(image_prompt, aspect_ratio="16:9")
        if not result:
            raise Exception("Empty result")
        return {"url": result}
    except Exception as e:
        import urllib.parse
        print(f"Gemini generation error fallback activated: {e}")
        pollinations_prompt = f"{style_directive} {enhanced_subject} highly detailed editorial photography"
        encoded = urllib.parse.quote(pollinations_prompt)
        return {"url": f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true&seed={variance_seed}"}

class ArticleResponse(BaseModel):
    title: str
    content: str
    images: List[str]
    sources: Optional[List[dict]] = None


# ─── LENGTH → TOKEN MAPPING ──────────────────────────────────────────
LENGTH_TOKEN_MAP = {
    "short":     1500,
    "medium":    3000,
    "long":      5000,
    "in-depth":  7000,
    "deep dive": 8000,
}

LENGTH_WORD_MAP = {
    "short":     "~500 words (3-4 sections)",
    "medium":    "~1,000 words (5-6 sections)",
    "long":      "~1,800 words (7-8 sections with sub-sections)",
    "in-depth":  "~2,500 words (8-10 sections with deep analysis, data tables, and expert quotes)",
    "deep dive": "~3,500+ words (10-12 sections, comprehensive guide with case studies, frameworks, and actionable steps)",
}

# ─── IMAGE STYLE DIRECTIVES ──────────────────────────────────────────
IMAGE_STYLE_MAP = {
    "Photorealistic": (
        "Photorealistic high-end editorial photograph, 8k resolution, cinematic lighting, ultra-detailed textures. "
        "Dynamic real-world composition with soft natural lens flares and professional shallow depth of field. "
        "Award-winning photography style. "
        "ABSOLUTELY NO TEXT, NO LETTERS, NO WORDS, NO WATERMARKS."
    ),
    "Illustration": (
        "High-quality digital illustration, vibrant saturated colors, bold outlines, trending on ArtStation and Behance. "
        "Professional editorial illustration style with dramatic composition. Clean vector-like quality with painterly textures. "
        "ABSOLUTELY NO TEXT, NO LETTERS, NO WORDS, NO WATERMARKS."
    ),
    "Minimalist": (
        "Ultra-clean minimalist design, flat illustration style, limited color palette of 3-4 harmonious colors, "
        "geometric shapes, negative space, modern graphic design aesthetic. Scandinavian design influence. "
        "ABSOLUTELY NO TEXT, NO LETTERS, NO WORDS, NO WATERMARKS."
    ),
    "3D Render": (
        "Professional 3D render, Octane Render, volumetric lighting, studio quality, isometric perspective, "
        "soft shadows, ambient occlusion, matte materials with subtle reflections, pastel color palette. "
        "ABSOLUTELY NO TEXT, NO LETTERS, NO WORDS, NO WATERMARKS."
    ),
    "Watercolor": (
        "Beautiful watercolor painting, soft washes, artistic brushstrokes, fine art quality, wet-on-wet technique, "
        "delicate color bleeding, textured watercolor paper visible, gallery exhibition quality. "
        "ABSOLUTELY NO TEXT, NO LETTERS, NO WORDS, NO WATERMARKS."
    ),
    "Flat Design": (
        "Modern flat design, Material Design inspired, clean geometric shapes, bold solid colors, long shadows, "
        "simple iconic elements, UI/UX design aesthetic, Google/Apple design language. "
        "ABSOLUTELY NO TEXT, NO LETTERS, NO WORDS, NO WATERMARKS."
    ),
    "Cinematic": (
        "Cinematic film still, anamorphic lens, dramatic chiaroscuro lighting, movie scene composition, "
        "35mm film grain, shallow depth of field, Blade Runner / Denis Villeneuve visual style, heavy atmosphere. "
        "ABSOLUTELY NO TEXT, NO LETTERS, NO WORDS, NO WATERMARKS."
    ),
    "Abstract": (
        "Bold abstract art, expressive brushstrokes, rich textures, contemporary gallery piece, "
        "dynamic composition with movement and energy, jewel-toned color palette, mixed media feel. "
        "ABSOLUTELY NO TEXT, NO LETTERS, NO WORDS, NO WATERMARKS."
    ),
    "Isometric": (
        "Detailed isometric 3D illustration, miniature world diorama, cute stylized objects, "
        "pastel colors, soft lighting, game-art inspired, pixel-perfect edges, cozy atmosphere. "
        "ABSOLUTELY NO TEXT, NO LETTERS, NO WORDS, NO WATERMARKS."
    ),
    "Editorial": (
        "High-end magazine editorial photography, studio lighting setup, commercial quality, "
        "dramatic shadows, rich contrast, Vogue/Bloomberg Businessweek aesthetic, professional retouching. "
        "ABSOLUTELY NO TEXT, NO LETTERS, NO WORDS, NO WATERMARKS."
    ),
}

PALETTES = [
    ("#1e3a5f", "#2563eb", "#60a5fa"),
    ("#1e3b2f", "#059669", "#34d399"),
    ("#3b1e5f", "#7c3aed", "#a78bfa"),
    ("#5f1e3a", "#dc2626", "#f87171"),
    ("#4a3728", "#d97706", "#fbbf24"),
    ("#1e4a5f", "#0891b2", "#22d3ee"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


# ─── WEB RESEARCH HELPERS ─────────────────────────────────────────────
async def _scrape_url(url: str) -> dict:
    """Scrape a single URL and return its title + cleaned text."""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers=HEADERS) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
            tag.decompose()
        title = soup.title.string.strip() if soup.title and soup.title.string else url
        main = soup.find("article") or soup.find("main") or soup.find("body")
        text = main.get_text(separator="\n", strip=True) if main else ""
        text = text[:4000]
        return {"url": url, "title": title, "text": text, "error": None}
    except Exception as e:
        return {"url": url, "title": url, "text": "", "error": str(e)}


async def _web_search(query: str, num_results: int = 5) -> List[dict]:
    """Search DuckDuckGo HTML for a query and scrape top results."""
    results = []
    try:
        search_url = "https://html.duckduckgo.com/html/"
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers=HEADERS) as client:
            resp = await client.post(search_url, data={"q": query})
        soup = BeautifulSoup(resp.text, "html.parser")
        links = []
        for a in soup.select("a.result__a"):
            href = a.get("href", "")
            if "uddg=" in href:
                from urllib.parse import unquote, urlparse, parse_qs
                parsed = parse_qs(urlparse(href).query)
                href = unquote(parsed.get("uddg", [href])[0])
            if href.startswith("http") and "duckduckgo" not in href:
                links.append(href)
            if len(links) >= num_results:
                break
        for url in links:
            data = await _scrape_url(url)
            if data["text"]:
                results.append(data)
    except Exception:
        pass
    return results


async def _gather_research(req: "ArticleRequest") -> tuple:
    """Gather web research from URLs or auto-search."""
    sources = []
    context_parts = []
    if req.source_urls:
        for url in req.source_urls[:5]:
            url = url.strip()
            if url:
                data = await _scrape_url(url)
                if data["text"]:
                    sources.append({"url": data["url"], "title": data["title"]})
                    context_parts.append(f"--- Source: {data['title']} ({data['url']}) ---\n{data['text']}")
    if req.web_research and req.topic:
        search_results = await _web_search(req.topic, num_results=4)
        for data in search_results:
            sources.append({"url": data["url"], "title": data["title"]})
            context_parts.append(f"--- Source: {data['title']} ({data['url']}) ---\n{data['text']}")
    context_text = "\n\n".join(context_parts) if context_parts else ""
    return context_text, sources


# ─── FALLBACK HELPERS ─────────────────────────────────────────────────
def _get_fallback_image() -> str:
    import urllib.parse
    import uuid
    variance_seed = uuid.uuid4().hex[:8]
    prompt = "A breathtaking, futuristic, highly conceptual editorial visualization of technology and business strategy"
    encoded = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true&seed={variance_seed}"

# Keep backward-compatible alias for other modules
_get_fallback_photorealistic_image = _get_fallback_image


def _generate_stellar_mock_article(topic: str, keywords: str, length: str) -> str:
    palette = PALETTES[hash(topic) % len(PALETTES)]
    t = topic.title() if topic else "Venture Ecosystems"
    tl = topic.lower() if topic else "venture ecosystems"
    html = f"""<h1 style="color:{palette[1]}">{t}: The Definitive Playbook for 2025 and Beyond</h1>

<p><em>A comprehensive deep-dive into {tl} — covering foundational frameworks, advanced strategies, real-world case studies, and a step-by-step implementation roadmap for leaders who refuse to settle for average outcomes.</em></p>

<h2>Executive Summary</h2>
<p>In an era defined by rapid disruption, understanding <strong>{tl}</strong> is no longer optional — it's the single most critical competency separating market leaders from laggards. This article covers the critical frameworks, emerging strategies, tactical implementation details, and battle-tested playbooks needed to master {tl} in today's hyper-competitive landscape.</p>

<blockquote style="border-left:4px solid {palette[1]};padding-left:16px;color:{palette[2]}">"{t} isn't just a trend — it's the foundation of the next generation of market leaders. The companies that understand this today will define the categories of tomorrow."</blockquote>

<h2>The Current Landscape: Where We Stand</h2>
<p>The {tl} ecosystem has undergone a seismic transformation over the past 24 months. Legacy approaches that dominated the previous decade are rapidly becoming obsolete, replaced by data-driven, AI-augmented methodologies that deliver 3-5x better outcomes at a fraction of the traditional cost.</p>
<p>Three macro-trends are reshaping the playing field:</p>
<ul>
<li><strong>Convergence of AI and domain expertise</strong> — The most successful players are those who combine deep industry knowledge with cutting-edge technological capabilities.</li>
<li><strong>Democratization of access</strong> — Tools and platforms that were once exclusive to Fortune 500 companies are now available to startups and mid-market players.</li>
<li><strong>Speed as the ultimate competitive moat</strong> — In a world where information asymmetry is shrinking, the ability to execute faster than competitors has become the primary differentiator.</li>
</ul>

<h2>Core Frameworks for Mastery</h2>
<h3>1. First-Principles Analysis</h3>
<p>Deconstructing {tl} to its atomic components reveals hidden leverage points that most practitioners overlook. Rather than applying best practices blindly, first-principles thinking forces you to question every assumption and rebuild your strategy from the ground up.</p>
<p>The process involves three phases: <strong>Decomposition</strong> (breaking the problem into fundamental truths), <strong>Reconstruction</strong> (building novel solutions from those truths), and <strong>Validation</strong> (testing against real-world data).</p>

<h3>2. Compounding Leverage Model</h3>
<p>Small daily optimizations — as little as 1% improvements — create exponential returns over time. This isn't theoretical. Companies that implement systematic improvement loops in their {tl} operations consistently outperform peers by 40-60% within 12 months.</p>

<h3>3. Ecosystem Mapping</h3>
<p>Identifying hidden value chains and untapped opportunities within the {tl} ecosystem requires a systematic approach to stakeholder analysis, competitive intelligence, and market gap identification. The most successful operators maintain living ecosystem maps that are updated weekly with fresh intelligence.</p>

<h2>Implementation Strategy: The 90-Day Playbook</h2>
<h3>Phase 1: Foundation (Weeks 1-4)</h3>
<p>Establish your baseline metrics, audit existing processes, and build the infrastructure for rapid experimentation. This phase is about creating the conditions for success rather than pursuing outcomes directly.</p>
<ul>
<li>Conduct a comprehensive audit of current {tl} operations</li>
<li>Identify the top 3 highest-leverage improvement opportunities</li>
<li>Build a measurement framework with leading and lagging indicators</li>
<li>Assemble a cross-functional tiger team with clear ownership</li>
</ul>

<h3>Phase 2: Acceleration (Weeks 5-8)</h3>
<p>Launch focused sprints targeting your highest-leverage opportunities. Use rapid experimentation cycles (test → measure → learn → iterate) to validate hypotheses and scale what works.</p>

<h3>Phase 3: Scale (Weeks 9-12)</h3>
<p>Systematize winning approaches, build automation where possible, and create playbooks that enable your entire organization to execute at the level of your best performers.</p>

<h2>Common Pitfalls and How to Avoid Them</h2>
<p>Even sophisticated operators fall into predictable traps when working with {tl}:</p>
<ul>
<li><strong>Analysis Paralysis</strong> — Over-optimizing strategy at the expense of execution. The cure: set hard deadlines for decision-making and embrace "good enough" in Phase 1.</li>
<li><strong>Shiny Object Syndrome</strong> — Chasing every new tool and technique instead of mastering fundamentals. The cure: maintain a strict "one new initiative at a time" policy.</li>
<li><strong>Measurement Myopia</strong> — Tracking vanity metrics instead of outcomes that matter. The cure: always connect metrics to revenue impact or customer value.</li>
</ul>

<h2>The Future: What's Coming Next</h2>
<p>Looking ahead, {tl} will be fundamentally reshaped by three forces: advanced AI capabilities, shifting regulatory landscapes, and evolving customer expectations. The organizations that begin preparing for these shifts today will have an insurmountable advantage when they arrive.</p>

<h2>Conclusion: Your Next Move</h2>
<p>Mastering {tl} requires disciplined execution, a willingness to iterate, and the courage to challenge conventional wisdom. The frameworks outlined above provide a battle-tested roadmap — but ultimately, the difference between reading about success and achieving it comes down to one thing: taking action.</p>

<p><strong>Start with Phase 1 this week. Your future self will thank you.</strong></p>"""
    return html


# ─── MAIN ENDPOINT ────────────────────────────────────────────────────
@router.post("/generate", response_model=ArticleResponse)
async def generate_article(req: ArticleRequest):
    # 0. Gather web research (if requested)
    research_context, sources = await _gather_research(req)

    # Resolve length settings
    length_key = req.length.lower().strip()
    max_tokens = LENGTH_TOKEN_MAP.get(length_key, 5000)
    length_desc = LENGTH_WORD_MAP.get(length_key, "~1,800 words (7-8 sections)")

    # 1. Generate Article using Anthropic
    if not settings.anthropic_api_key or "your-" in settings.anthropic_api_key:
        content_html = _generate_stellar_mock_article(req.topic or "Venture Ecosystems", req.keywords, req.length)
        title = f"{req.topic.title()} - Comprehensive Analysis" if req.topic else "Generated Analysis"
    else:
        anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

        video_context = f" Base heavily on the content, sentiment, and themes from this video link: {req.video_url}." if req.video_url else ""
        topic_context = f" The topic is '{req.topic}'." if req.topic else " Choose a highly relevant, compelling venture capital or startup framework angle automatically."

        # Build research block
        research_block = ""
        if research_context:
            research_block = (
                f"\n\n--- WEB RESEARCH DATA ---\n"
                f"Use the following real-world data, facts, statistics, and insights gathered from web research "
                f"to make the article factual, data-driven, and authoritative. Cite specific facts and numbers. "
                f"Do NOT fabricate statistics — only use what's provided below:\n\n"
                f"{research_context[:10000]}\n"
                f"--- END RESEARCH DATA ---\n"
            )

        prompt = (
            f"You are an elite content strategist and long-form writer. Write a comprehensive, publication-ready "
            f"{req.platform} post.{topic_context}\n\n"
            f"Keywords to weave naturally throughout: {req.keywords}.\n"
            f"Tone: '{req.tone}'.\n"
            f"Target length: {length_desc}. THIS IS CRITICAL — you MUST write the FULL length requested. "
            f"Do NOT cut short. Fill every section with rich, substantive content.\n"
            f"{video_context}"
            f"{research_block}\n\n"
            f"STRUCTURE REQUIREMENTS:\n"
            f"- Start with a compelling <h1> title\n"
            f"- Include an executive summary / hook paragraph that grabs attention immediately\n"
            f"- Use <h2> for major sections and <h3> for sub-sections\n"
            f"- Include at least one <blockquote> with a powerful, relevant quote\n"
            f"- Use <ul>/<li> for lists, <strong> for emphasis, <em> for nuance\n"
            f"- Include specific numbers, percentages, frameworks, and actionable advice\n"
            f"- End with a compelling conclusion and clear call-to-action\n"
            f"- Make it feel like a premium article from Harvard Business Review or First Round Review\n\n"
            f"FORMAT: Output ONLY valid HTML. No markdown. No code fences. Start directly with <h1>."
        )

        if sources:
            prompt += (
                f"\n\nAt the end of the article, add a 'Sources' section with an <h3>Sources</h3> heading "
                f"and a list of the referenced URLs as clickable links."
            )

        try:
            response = await anthropic_client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=max_tokens,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            content_html = response.content[0].text
            title = req.topic.title() if req.topic else f"{req.platform} Content"
        except Exception as e:
            print(f"Anthropic generation failed: {str(e)}")
            content_html = _generate_stellar_mock_article(req.topic or "Venture Ecosystems", req.keywords, req.length)
            title = f"{req.topic.title()} - Generated Analysis" if req.topic else "Generated Analysis"

    # 2. Generate Image using Gemini Imagen or Pollinations
    from app.core.gemini_images import generate_image_gemini
    has_gemini = settings.gemini_api_key and "your-" not in settings.gemini_api_key

    style_directive = IMAGE_STYLE_MAP.get(req.image_style, IMAGE_STYLE_MAP["Photorealistic"])
    subject_word = req.topic or "technology and innovation"

    # Try to get a better subject from Anthropic if available
    if settings.anthropic_api_key and "your-" not in (settings.anthropic_api_key or "your-"):
        try:
            anthropic_client_img = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            img_prompt_req = (
                f"Based on this article, output ONLY a 3-5 word visual scene description that captures "
                f"the core theme (e.g. 'futuristic healthcare lab', 'bustling fintech trading floor'). "
                f"Nothing else:\n\n{content_html[:1500]}"
            )
            img_prompt_res = await anthropic_client_img.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=30,
                temperature=0.3,
                messages=[{"role": "user", "content": img_prompt_req}]
            )
            subject_word = img_prompt_res.content[0].text.strip()
        except Exception:
            pass

    import time
    import urllib.parse
    import random
    images = []
    is_draft = getattr(req, "image_quality", "draft") == "draft"
    
    concrete_visuals = [
        "modern business executives analyzing market data over a glass architectural table",
        "a focused entrepreneur sketching architectural diagrams on a clean whiteboard",
        "a bustling creative agency office scene infused with warm natural sunlight",
        "premium venture capital board meeting with dramatic professional lighting",
        "close-up portrait of a visionary leader looking thoughtfully through a skyscraper window",
        "sleek minimalist workspace with organic trailing plants and architectural blueprints",
        "innovative tech founders collaborating over documents in an industrial loft",
        "dynamic wide-angle shot of a premium corporate lobby bustling with professionals"
    ]
    enhanced_subject = f"{subject_word}. Visual Scene: {random.choice(concrete_visuals)}"
        
    for index in range(1):
        import uuid
        variance_seed = uuid.uuid4().hex[:8]
        
        # Determine if we should forcefully override to draft because of missing gemini api keys
        should_use_draft = is_draft or not has_gemini
        
        if should_use_draft:
            pollinations_prompt = f"{style_directive} {enhanced_subject} highly detailed editorial photography"
            encoded = urllib.parse.quote(pollinations_prompt)
            images.append(f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true&seed={variance_seed}")
        else:
            image_prompt = (
                f"ABSOLUTE DIRECTIVE: Make this visually UNIQUE compared to typical generations. "
                f"Inject radical creative flair. [SEED: {variance_seed}] [Enforcer ID: {index+1}]\n\n"
                f"STYLE GUIDANCE: {style_directive}\n\n"
                f"SCENE TO REPRESENT: {enhanced_subject}."
            )
            try:
                result = await generate_image_gemini(image_prompt, aspect_ratio="16:9")
                if not result:
                    print("Gemini returned None, activating dynamic fallback...")
                    pollinations_prompt = f"{style_directive} {subject_word} premium editorial photography"
                    encoded = urllib.parse.quote(pollinations_prompt)
                    images.append(f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true&seed={variance_seed}")
                else:
                    images.append(result)
            except Exception as e:
                print(f"Gemini fallback activated: {str(e)}")
                # Dynamic ultra-fallback without using local static stock image:
                pollinations_prompt = f"{style_directive} {subject_word} editorial concept"
                encoded = urllib.parse.quote(pollinations_prompt)
                images.append(f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true&seed={variance_seed}")
            await asyncio.sleep(1.5)

    return ArticleResponse(title=title, content=content_html, images=images, sources=sources if sources else None)

