import hashlib
import base64
import math
from fastapi import APIRouter
from pydantic import BaseModel
import anthropic
from openai import AsyncOpenAI
from app.core.config import settings

router = APIRouter(prefix="/api/articles", tags=["articles"])


class ArticleRequest(BaseModel):
    platform: str = "Article"
    topic: str = ""
    keywords: str = ""
    tone: str = "professional"
    length: str = "medium"
    video_url: str = ""
    image_style: str = "Photorealistic"


class ArticleResponse(BaseModel):
    title: str
    content: str
    image: str


LENGTH_MAP = {
    "short": 3,
    "medium": 5,
    "long": 8,
}

PALETTES = [
    ("#1e3a5f", "#2563eb", "#60a5fa"),
    ("#1e3b2f", "#059669", "#34d399"),
    ("#3b1e5f", "#7c3aed", "#a78bfa"),
    ("#5f1e3a", "#dc2626", "#f87171"),
    ("#4a3728", "#d97706", "#fbbf24"),
    ("#1e4a5f", "#0891b2", "#22d3ee"),
]


def _get_fallback_photorealistic_image() -> str:
    # Beautiful, photorealistic dynamic unslash placeholder fitting the startup/tech/AI aesthetic
    return "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=1024&h=1024&auto=format&fit=crop"


def _generate_stellar_mock_article(topic: str, keywords: str) -> str:
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    kw_str = ", ".join(kw_list) if kw_list else "innovation, growth, technology"
    
    html = f"<h1>The Ultimate Guide: Unpacking {topic.title()}</h1>"
    html += f'<p class="lead" style="font-size: 1.25em; color: #94a3b8; font-style: italic;">An inside look into how {topic.lower()} is fundamentally reshaping the modern business ecosystem, driven by principles like {kw_str}.</p>'
    html += f"<h2>1. Introduction into {topic}</h2>"
    html += f"<p>The landscape of modern industries is changing at an unprecedented pace. Organizations worldwide are pivoting their core strategies to leverage the phenomenal power of <strong>{topic}</strong>. Historically, shifts of this magnitude only occurred once every few decades. Today, guided by agile frameworks and technological breakthroughs, {topic} is not just an operational necessity—it is the bedrock of future innovation.</p>"
    html += f"<p>When assessing how deeply {topic} embeds itself into cultural and economic frameworks, we have to look past the surface-level metrics. It requires an exploration of deep-rooted infrastructural integrations. From venture capital deployment to granular consumer analytics, the implications are staggering. We are witnessing the dawn of an entirely new asset paradigm.</p>"
    
    html += f"<h2>2. Core Drivers and Strategic Implementations</h2>"
    html += f"<p>Understanding the \"why\" is crucial. The primary drivers pushing <em>{topic}</em> to the forefront include rapid digitalization, shifting consumer expectations, and an increasing demand for scalable solutions.</p>"
    html += f"<ul>"
    html += f"<li><b>Decentralized Adaptability:</b> Operations can now pivot on a dime. This flexibility is largely powered by integrating foundational components related to {topic}.</li>"
    html += f"<li><b>Resource Optimization:</b> Capital efficiency has skyrocketed as machine-driven heuristics take over redundant workflows.</li>"
    html += f"<li><b>Ecosystem Synergy:</b> Competitors are now collaborators. The API-first economy means platforms interconnect effortlessly.</li>"
    html += f"</ul>"
    
    html += f"<h2>3. The Analytics Perspective</h2>"
    html += f"<p>Data without insight is just noise. The intersection of our core subject—{topic}—with advanced machine learning models allows predictive horizons that were previously unimaginable. Instead of merely reacting to quarterly losses, visionary firms accurately preempt market shifts.</p>"
    html += f"<blockquote>\"To ignore {topic} is to ignore the future. The data conclusively dictates where capital should flow, and right now, the momentum is undeniable.\" — <em>Industry Leading Analyst</em></blockquote>"
    
    html += f"<h2>4. Actionable Steps for Enterprise Integration</h2>"
    html += f"<p>So how does a legacy corporation or a burgeoning seed-stage startup begin mapping their transition towards {topic}? It begins with structural alignment.</p>"
    html += f"<ol>"
    html += f"<li><strong>Audit Current Infrastructure:</strong> Identify bottlenecks that {topic} can directly alleviate.</li>"
    html += f"<li><strong>Establish KPIs:</strong> Quantify what success looks like over a 3, 6, and 12-month trajectory.</li>"
    html += f"<li><strong>Empower Teams:</strong> Upskill internal talent to ensure they understand the nuances of the strategic realignment.</li>"
    html += f"<li><strong>Deploy and Iterate:</strong> Release in discrete phases. Monitor the impact. Optimize.</li>"
    html += f"</ol>"
    
    html += f"<h2>5. Looking Over the Horizon</h2>"
    html += f"<p>We are merely scratching the surface. In the next five years, elements of {kw_str} will not just be add-ons; they will be the fundamental pillars upon which entirely new economic structures are built. Engaging deeply with {topic} ensures that organizations don't just survive the coming wave—they ride it.</p>"
    html += f"<p>The time to act is now. Welcome to the future of enterprise execution.</p>"
    return html

@router.post("/generate", response_model=ArticleResponse)
async def generate_article(req: ArticleRequest):
    # 1. Generate Article using Anthropic
    if not settings.anthropic_api_key or "your-" in settings.anthropic_api_key:
        content_html = _generate_stellar_mock_article(req.topic or "Venture Ecosystems", req.keywords)
        title = f"{req.topic.title()} - Comprehensive Analysis" if req.topic else "Generated Analysis"
    else:
        anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        
        video_context = f" Base heavily on the content, sentiment, and themes from this video link: {req.video_url}." if req.video_url else ""
        topic_context = f" The topic is '{req.topic}'." if req.topic else " Choose a highly relevant, compelling venture capital or startup framework angle automatically."
        prompt = f"Please write a highly comprehensive {req.platform} post.{topic_context} Keywords to include: {req.keywords}. The tone should be '{req.tone}'. Target length: '{req.length}'.{video_context} Format the response entirely in structured, beautiful HTML (using h2, h3, ul, blockquotes) without wrapping inside Markdown blocks. Make the first line an elegant <h1> tag."
        
        response = await anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        content_html = response.content[0].text
        title = req.topic.title() if req.topic else f"{req.platform} Content"

    # 2. Generate Image using OpenAI
    if not settings.openai_api_key or "your-" in settings.openai_api_key:
        # If API missing, return my photorealistic aesthetic URL instead of SVGs
        image_url = _get_fallback_photorealistic_image()
    else:
        openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        # If we have Anthropic, derive the image target dynamically from the article
        # Core aesthetic directive matching the reference style:
        # Clean modern desk, laptop with cyan HUD, floating translucent holograms, golden hour bokeh window
        STYLE_DIRECTIVE = (
            "Photorealistic editorial photograph. Scene: a sleek modern minimalist desk near a large floor-to-ceiling window. "
            "On the desk sits an open silver laptop displaying a glowing cyan circular HUD interface on its dark screen. "
            "Floating above and around the laptop are translucent holographic elements: a small glowing wireframe globe, interconnected data nodes, "
            "and faint circuit-board line patterns, all rendered in soft cyan and green glow. "
            "A small desk globe, a pen holder, and a wireless mouse sit beside the laptop. "
            "Lighting: warm golden hour sunlight streams through the window creating heavy circular bokeh and soft lens flares. "
            "The overall palette is muted and desaturated with pops of cyan and green from the holographic elements. "
            "Shallow depth of field with the background softly blurred. "
            "ABSOLUTELY NO TEXT, NO LETTERS, NO WORDS, NO WATERMARKS IN THE IMAGE."
        )

        if not settings.anthropic_api_key or "your-" in settings.anthropic_api_key:
            image_prompt = f"{STYLE_DIRECTIVE} The holographic HUD elements should subtly reference the topic of: {req.topic}."
        else:
            img_prompt_req = f"Based on this article, output ONLY 1-2 words describing the core industry or subject (e.g. 'healthcare', 'fintech', 'robotics'). Nothing else:\n\n{content_html[:1000]}"
            img_prompt_res = await anthropic_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=20,
                temperature=0.3,
                messages=[{"role": "user", "content": img_prompt_req}]
            )
            subject_word = img_prompt_res.content[0].text.strip()
            image_prompt = f"{STYLE_DIRECTIVE} The holographic HUD elements should subtly reference the industry of: {subject_word}."
        
        
        try:
            img_response = await openai_client.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                n=1,
                size="1024x1024"
            )
            image_url = img_response.data[0].url
        except Exception:
            # Fallback on generic failure
            image_url = _get_fallback_photorealistic_image()

    return ArticleResponse(title=title, content=content_html, image=image_url)
