import asyncio
import logging
import anthropic
from openai import AsyncOpenAI
from app.tasks.celery_app import celery_app
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import ContentItem, Company
from app.core.config import settings

logger = logging.getLogger(__name__)


async def _generate_article_async(content_item_id: str):
    async with AsyncSessionLocal() as db:
        # Fetch content item
        stmt = select(ContentItem).where(ContentItem.id == content_item_id)
        result = await db.execute(stmt)
        content_item = result.scalar_one_or_none()
        
        if not content_item:
            return {"error": "Content item not found"}
        
        try:
            from app.routes.articles import _generate_stellar_mock_article, _get_fallback_photorealistic_image
            # 1. Generate Article using Anthropic
            if not settings.anthropic_api_key or "your-" in settings.anthropic_api_key:
                logger.info("Using stellar offline Anthropic mock")
                content_html = _generate_stellar_mock_article(content_item.topic, "")
            else:
                anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
                prompt = f"Please write a highly comprehensive article for the platform '{content_item.platform}'. The topic is '{content_item.topic}' and the tone should be '{content_item.tone}'. Target word count: ~{content_item.target_length} words. Format the response entirely in structured, beautiful HTML (using h2, h3, ul, blockquotes) without wrapping inside Markdown blocks. Ensure the first line is an elegant <h1> tag."
                
                anthropic_response = await anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=4000,
                    temperature=0.7,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                content_html = anthropic_response.content[0].text
                
            content_item.content_html = content_html
            content_item.content_body = content_html
            
            # 2. Generate Image using OpenAI
            if not settings.openai_api_key or "your-" in settings.openai_api_key:
                logger.info("Using offline Unsplash DALL-E fallback")
                content_item.image_url = _get_fallback_photorealistic_image()
            else:
                openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
                
                # Dynamically derive image prompt from the high-quality article body
                if not settings.anthropic_api_key or "your-" in settings.anthropic_api_key:
                    image_prompt = f"A photorealistic, highly detailed style image showcasing: {content_item.topic}. DO NOT include any text, words, or letters in the image."
                else:
                    img_prompt_req = f"Based on this article snippet, safely output ONLY a visually stunning, concise (under 40 words) description for a photorealistic image generation model. It must depict a vivid, physical scene or specific object strictly described or heavily thematic to this text. DO NOT describe any signs, labels, or text whatsoever:\n\n{content_html[:2000]}"
                    img_prompt_res = await anthropic_client.messages.create(
                        model="claude-3-5-sonnet-20240620",
                        max_tokens=100,
                        temperature=0.7,
                        messages=[{"role": "user", "content": img_prompt_req}]
                    )
                    image_prompt = f"Photorealistic, highly detailed style. DO NOT include any text, words, labels, or letters in the image: {img_prompt_res.content[0].text.strip()}"
                
                try:
                    img_response = await openai_client.images.generate(
                        model="dall-e-3",
                        prompt=image_prompt,
                        n=1,
                        size="1024x1024"
                    )
                    content_item.image_url = img_response.data[0].url
                except Exception as e:
                    logger.error(f"OpenAI Image Gen Error: {e}")
                    content_item.image_url = _get_fallback_photorealistic_image()
            
            content_item.status = "review"
            await db.commit()
            return {"status": "completed", "content_id": str(content_item_id)}
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            content_item.status = "failed"
            await db.commit()
            return {"error": str(e)}

@celery_app.task
def generate_article(content_item_id: str):
    """Generate article content using AI."""
    return asyncio.run(_generate_article_async(content_item_id))


async def _discover_topics_async(company_id: str):
    # TODO: Crawl company website, check GSC, analyze competitors
    return {
        "status": "completed",
        "company_id": str(company_id),
        "topics": [],
    }

@celery_app.task
def discover_topics(company_id: str):
    """Discover content topics for a company."""
    return asyncio.run(_discover_topics_async(company_id))


async def _run_seo_scan_async(company_id: str):
    # TODO: Crawl site, check technical SEO, legal compliance
    return {
        "status": "completed",
        "company_id": str(company_id),
    }

@celery_app.task
def run_seo_scan(company_id: str):
    """Run SEO scan for a company."""
    return asyncio.run(_run_seo_scan_async(company_id))


async def _adapt_content_to_platform_async(content_item_id: str, platform: str):
    async with AsyncSessionLocal() as db:
        stmt = select(ContentItem).where(ContentItem.id == content_item_id)
        result = await db.execute(stmt)
        content_item = result.scalar_one_or_none()
        
        if not content_item:
            return {"error": "Content item not found"}
        
        # TODO: Adapt content using AI
        
        return {
            "status": "completed",
            "platform": platform,
        }

@celery_app.task
def adapt_content_to_platform(content_item_id: str, platform: str):
    """Adapt content to different platform (LinkedIn, Instagram, etc)."""
    return asyncio.run(_adapt_content_to_platform_async(content_item_id, platform))
