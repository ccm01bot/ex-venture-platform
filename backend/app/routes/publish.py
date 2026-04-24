from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import httpx
import base64
import json

from app.core.database import get_db
from app.models import Company

router = APIRouter(prefix="/api/publish", tags=["publish"])

class PublishRequest(BaseModel):
    title: str
    content_html: str
    hero_image_url: str = ""

@router.post("/{company_id}")
async def publish_article(
    company_id: str,
    req: PublishRequest,
    db: AsyncSession = Depends(get_db)
):
    """Publish an article to a configured CMS platform for the company."""
    # Find company config
    stmt = select(Company).where(Company.id == company_id)
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if not company.cms_platform or company.cms_platform == "none":
        raise HTTPException(status_code=400, detail="Company does not have a configured CMS platform.")

    platform = company.cms_platform.lower()

    if platform == "wordpress":
        if not company.cms_url or not company.cms_api_key:
            raise HTTPException(status_code=400, detail="Missing WordPress URL or App Password.")
        
        # WordPress expected Application Passwords format: "username:password"
        # Since we just collect one string in the UI, we assume they paste the base64 encoded string
        # or we just encode it here if it contains a colon.
        auth_string = company.cms_api_key
        if ":" in auth_string:
            auth_encoded = base64.b64encode(auth_string.encode()).decode()
        else:
            auth_encoded = auth_string
            
        base_url = company.cms_url.strip().rstrip("/")
        # usually https://site.com/wp-json/wp/v2/posts
        if not base_url.endswith("/wp/v2"):
            if base_url.endswith("/wp-json"):
                base_url += "/wp/v2"
            else:
                base_url += "/wp-json/wp/v2"

        # Note: True WordPress image side-loading is complex (requires media upload first).
        # We will embed the external Image statically in the content body as an MVP.
        hero_tag = f'<img src="{req.hero_image_url}" alt="Hero" style="width:100%; border-radius: 8px; margin-bottom: 20px;" />' if req.hero_image_url else ''
        wp_html = f"{hero_tag}\n{req.content_html}"

        wp_payload = {
            "title": req.title,
            "content": wp_html,
            "status": "draft" # Default to draft for safety allowing user review
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{base_url}/posts",
                    json=wp_payload,
                    headers={
                        "Authorization": f"Basic {auth_encoded}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                if not resp.is_success:
                    print(resp.text)
                    raise HTTPException(status_code=400, detail=f"WordPress API error: {resp.text}")
                
                data = resp.json()
                return {"status": "success", "publish_url": data.get("link"), "provider": "wordpress"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to post to WordPress: {str(e)}")

    elif platform == "webhook":
        if not company.cms_url:
            raise HTTPException(status_code=400, detail="Missing Webhook URL.")

        payload = {
            "event": "article_published",
            "company_name": company.name,
            "topic": req.title,
            "content_html": req.content_html,
            "hero_image_url": req.hero_image_url,
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    company.cms_url,
                    json=payload,
                    timeout=15.0
                )
                return {"status": "success", "publish_url": company.cms_url, "provider": "webhook"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to trigger Webhook: {str(e)}")

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported CMS platform: {platform}")
