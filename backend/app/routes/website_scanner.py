"""Real website SEO scanner — scrapes a URL and returns structured data."""
import asyncio
import logging
import re
import time
from datetime import datetime
from urllib.parse import urlparse, urljoin

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Any
import anthropic
import json
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scan", tags=["scan"])


class ScanRequest(BaseModel):
    url: str

class AiFixRequest(BaseModel):
    company_id: str
    scan_data: Any

class AiFixResponse(BaseModel):
    optimized_title: str
    optimized_meta: str
    action_plan: str


class ScanResult(BaseModel):
    url: str
    status_code: int
    load_time_ms: int
    # Meta
    title: Optional[str] = None
    title_length: int = 0
    meta_description: Optional[str] = None
    meta_description_length: int = 0
    canonical: Optional[str] = None
    favicon: Optional[str] = None
    language: Optional[str] = None
    # Headings
    h1_tags: list[str] = []
    h2_tags: list[str] = []
    h3_tags: list[str] = []
    heading_count: int = 0
    # Content
    word_count: int = 0
    text_to_html_ratio: float = 0.0
    # Images
    total_images: int = 0
    images_without_alt: int = 0
    image_details: list[dict] = []
    # Links
    internal_links: int = 0
    external_links: int = 0
    broken_links: list[str] = []
    # Technical
    has_ssl: bool = False
    has_viewport: bool = False
    has_robots_txt: bool = False
    has_sitemap: bool = False
    has_og_tags: bool = False
    has_twitter_cards: bool = False
    has_schema_markup: bool = False
    has_google_analytics: bool = False
    has_favicon: bool = False
    charset: Optional[str] = None
    # Performance hints
    total_page_size_kb: float = 0.0
    inline_css_count: int = 0
    inline_js_count: int = 0
    external_css_count: int = 0
    external_js_count: int = 0
    # Social
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    twitter_card: Optional[str] = None
    # Score
    seo_score: int = 0
    issues: list[dict] = []
    passes: list[str] = []


async def _check_url_exists(client: httpx.AsyncClient, url: str) -> bool:
    try:
        r = await client.head(url, follow_redirects=True, timeout=5)
        return r.status_code < 400
    except Exception:
        return False


@router.post("/website", response_model=ScanResult)
async def scan_website(req: ScanRequest):
    """Scrape a website and return comprehensive SEO data."""
    url = req.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    base_domain = f"{parsed.scheme}://{parsed.netloc}"
    issues: list[dict] = []
    passes: list[str] = []
    score = 100  # Start at 100, deduct for issues

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=15,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
    ) as client:
        # ── Fetch Main Page ────────────────────────────────────
        start = time.time()
        try:
            resp = await client.get(url)
        except Exception as e:
            return ScanResult(
                url=url, status_code=0, load_time_ms=0,
                issues=[{"severity": "critical", "message": f"Could not reach website: {str(e)}"}],
                seo_score=0,
            )
        load_time = int((time.time() - start) * 1000)
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")
        page_size_kb = round(len(resp.content) / 1024, 1)

        # ── STATUS CODE ────────────────────────────────────────
        status_code = resp.status_code
        if status_code != 200:
            issues.append({"severity": "critical", "message": f"HTTP status code is {status_code} (expected 200)"})
            score -= 15

        # ── TITLE ──────────────────────────────────────────────
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else None
        title_len = len(title) if title else 0
        if not title:
            issues.append({"severity": "critical", "message": "Missing page title"})
            score -= 10
        elif title_len < 30:
            issues.append({"severity": "warning", "message": f"Title too short ({title_len} chars, recommend 50-60)"})
            score -= 3
        elif title_len > 60:
            issues.append({"severity": "warning", "message": f"Title too long ({title_len} chars, recommend 50-60)"})
            score -= 3
        else:
            passes.append("Title tag is optimal length")

        # ── META DESCRIPTION ───────────────────────────────────
        meta_desc_tag = soup.find("meta", attrs={"name": "description"})
        meta_desc = meta_desc_tag.get("content", "").strip() if meta_desc_tag else None
        meta_desc_len = len(meta_desc) if meta_desc else 0
        if not meta_desc:
            issues.append({"severity": "critical", "message": "Missing meta description"})
            score -= 10
        elif meta_desc_len < 120:
            issues.append({"severity": "warning", "message": f"Meta description too short ({meta_desc_len} chars, recommend 150-160)"})
            score -= 3
        elif meta_desc_len > 160:
            issues.append({"severity": "warning", "message": f"Meta description too long ({meta_desc_len} chars, recommend 150-160)"})
            score -= 3
        else:
            passes.append("Meta description is optimal length")

        # ── CANONICAL ──────────────────────────────────────────
        canonical_tag = soup.find("link", rel="canonical")
        canonical = canonical_tag.get("href") if canonical_tag else None
        if not canonical:
            issues.append({"severity": "warning", "message": "No canonical tag found"})
            score -= 3
        else:
            passes.append("Canonical tag present")

        # ── LANGUAGE ───────────────────────────────────────────
        html_tag = soup.find("html")
        language = html_tag.get("lang") if html_tag else None
        if not language:
            issues.append({"severity": "info", "message": "No lang attribute on <html> tag"})
            score -= 2
        else:
            passes.append(f"Language declared: {language}")

        # ── CHARSET ────────────────────────────────────────────
        charset_tag = soup.find("meta", attrs={"charset": True})
        charset = charset_tag.get("charset") if charset_tag else None
        if not charset:
            ct_tag = soup.find("meta", attrs={"http-equiv": re.compile("content-type", re.I)})
            if ct_tag:
                charset = "utf-8"  # present

        # ── HEADINGS ───────────────────────────────────────────
        h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
        h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]
        h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3")]
        heading_count = len(h1_tags) + len(h2_tags) + len(h3_tags)
        
        if len(h1_tags) == 0:
            issues.append({"severity": "critical", "message": "No H1 tag found — essential for SEO"})
            score -= 10
        elif len(h1_tags) > 1:
            issues.append({"severity": "warning", "message": f"Multiple H1 tags found ({len(h1_tags)}) — use exactly one"})
            score -= 5
        else:
            passes.append("Single H1 tag present")

        if len(h2_tags) == 0:
            issues.append({"severity": "info", "message": "No H2 tags found — add subheadings for structure"})
            score -= 2

        # ── CONTENT ────────────────────────────────────────────
        body = soup.find("body")
        text_content = body.get_text(separator=" ", strip=True) if body else ""
        word_count = len(text_content.split())
        text_ratio = round((len(text_content) / max(len(html), 1)) * 100, 1)

        if word_count < 300:
            issues.append({"severity": "warning", "message": f"Low word count ({word_count}) — more content helps rankings"})
            score -= 5
        else:
            passes.append(f"Good content volume ({word_count} words)")

        if text_ratio < 10:
            issues.append({"severity": "info", "message": f"Low text-to-HTML ratio ({text_ratio}%) — could indicate bloated code"})
            score -= 2

        # ── IMAGES ─────────────────────────────────────────────
        images = soup.find_all("img")
        total_images = len(images)
        images_no_alt = []
        image_details = []
        for img in images[:20]:  # Cap at 20
            src = img.get("src", "")
            alt = img.get("alt", "")
            if src:
                image_details.append({"src": src[:100], "alt": alt, "has_alt": bool(alt.strip())})
            if not alt or not alt.strip():
                images_no_alt.append(src)

        missing_alt_count = len(images_no_alt)
        if total_images > 0 and missing_alt_count > 0:
            pct = int(missing_alt_count / total_images * 100)
            issues.append({"severity": "warning", "message": f"{missing_alt_count}/{total_images} images missing alt text ({pct}%)"})
            score -= min(8, missing_alt_count * 2)
        elif total_images > 0:
            passes.append("All images have alt text")

        # ── LINKS ──────────────────────────────────────────────
        all_links = soup.find_all("a", href=True)
        internal = 0
        external = 0
        for link in all_links:
            href = link.get("href", "")
            if href.startswith(("mailto:", "tel:", "javascript:", "#")):
                continue
            full_url = urljoin(url, href)
            link_parsed = urlparse(full_url)
            if link_parsed.netloc == parsed.netloc:
                internal += 1
            else:
                external += 1

        # ── VIEWPORT ───────────────────────────────────────────
        viewport = soup.find("meta", attrs={"name": "viewport"})
        has_viewport = viewport is not None
        if not has_viewport:
            issues.append({"severity": "critical", "message": "No viewport meta tag — site may not be mobile-friendly"})
            score -= 8
        else:
            passes.append("Mobile viewport tag present")

        # ── SSL ────────────────────────────────────────────────
        has_ssl = url.startswith("https://")
        if not has_ssl:
            issues.append({"severity": "critical", "message": "Site not using HTTPS"})
            score -= 10
        else:
            passes.append("HTTPS/SSL active")

        # ── OG TAGS ────────────────────────────────────────────
        og_title_tag = soup.find("meta", property="og:title")
        og_desc_tag = soup.find("meta", property="og:description")
        og_image_tag = soup.find("meta", property="og:image")
        has_og = og_title_tag is not None
        og_title = og_title_tag.get("content") if og_title_tag else None
        og_desc = og_desc_tag.get("content") if og_desc_tag else None
        og_image = og_image_tag.get("content") if og_image_tag else None
        if not has_og:
            issues.append({"severity": "warning", "message": "No Open Graph tags — links won't preview on social media"})
            score -= 5
        else:
            passes.append("Open Graph tags present")

        # ── TWITTER CARDS ──────────────────────────────────────
        twitter_card_tag = soup.find("meta", attrs={"name": "twitter:card"})
        has_twitter = twitter_card_tag is not None
        twitter_card = twitter_card_tag.get("content") if twitter_card_tag else None
        if not has_twitter:
            issues.append({"severity": "info", "message": "No Twitter Card tags"})
            score -= 2

        # ── SCHEMA MARKUP ──────────────────────────────────────
        has_schema = bool(soup.find("script", type="application/ld+json"))
        if not has_schema:
            issues.append({"severity": "info", "message": "No structured data (JSON-LD) found"})
            score -= 3
        else:
            passes.append("Structured data (JSON-LD) present")

        # ── FAVICON ────────────────────────────────────────────
        fav = soup.find("link", rel=re.compile("icon", re.I))
        favicon = fav.get("href") if fav else None
        has_favicon = favicon is not None
        if not has_favicon:
            issues.append({"severity": "info", "message": "No favicon found"})
            score -= 1

        # ── GOOGLE ANALYTICS ───────────────────────────────────
        has_ga = bool(re.search(r"(gtag|google-analytics|googletagmanager|GA_TRACKING_ID|G-[A-Z0-9]+)", html, re.I))

        # ── INLINE/EXTERNAL CSS & JS ───────────────────────────
        inline_css = len(soup.find_all("style"))
        inline_js = len(soup.find_all("script", src=False))
        ext_css = len(soup.find_all("link", rel="stylesheet"))
        ext_js = len(soup.find_all("script", src=True))

        # ── ROBOTS.TXT & SITEMAP ───────────────────────────────
        has_robots, has_sitemap = await asyncio.gather(
            _check_url_exists(client, base_domain + "/robots.txt"),
            _check_url_exists(client, base_domain + "/sitemap.xml"),
        )
        if not has_robots:
            issues.append({"severity": "info", "message": "No robots.txt found"})
            score -= 2
        else:
            passes.append("robots.txt present")
        if not has_sitemap:
            issues.append({"severity": "warning", "message": "No sitemap.xml found"})
            score -= 3
        else:
            passes.append("sitemap.xml present")

        # ── LOAD TIME ──────────────────────────────────────────
        if load_time > 3000:
            issues.append({"severity": "warning", "message": f"Slow page load ({load_time}ms) — aim for under 3 seconds"})
            score -= 5
        elif load_time > 1500:
            issues.append({"severity": "info", "message": f"Page load is okay ({load_time}ms) — aim for under 1.5 seconds"})
            score -= 2
        else:
            passes.append(f"Fast load time ({load_time}ms)")

        score = max(0, min(100, score))

        return ScanResult(
            url=url,
            status_code=status_code,
            load_time_ms=load_time,
            title=title,
            title_length=title_len,
            meta_description=meta_desc,
            meta_description_length=meta_desc_len,
            canonical=canonical,
            favicon=favicon,
            language=language,
            h1_tags=h1_tags,
            h2_tags=h2_tags[:10],
            h3_tags=h3_tags[:10],
            heading_count=heading_count,
            word_count=word_count,
            text_to_html_ratio=text_ratio,
            total_images=total_images,
            images_without_alt=missing_alt_count,
            image_details=image_details,
            internal_links=internal,
            external_links=external,
            has_ssl=has_ssl,
            has_viewport=has_viewport,
            has_robots_txt=has_robots,
            has_sitemap=has_sitemap,
            has_og_tags=has_og,
            has_twitter_cards=has_twitter,
            has_schema_markup=has_schema,
            has_google_analytics=has_ga,
            has_favicon=has_favicon,
            charset=charset,
            total_page_size_kb=page_size_kb,
            inline_css_count=inline_css,
            inline_js_count=inline_js,
            external_css_count=ext_css,
            external_js_count=ext_js,
            og_title=og_title,
            og_description=og_desc,
            og_image=og_image,
            twitter_card=twitter_card,
            seo_score=score,
            issues=issues,
            passes=passes,
        )

@router.post("/fix-seo", response_model=AiFixResponse)
async def generate_seo_fixes(req: AiFixRequest):
    """Feed the massive explicit SEO array structurally into Claude to dynamically generate HTML and Meta remediation setups."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return AiFixResponse(
            optimized_title="Missing Anthropic API Key",
            optimized_meta="Please add ANTHROPIC_API_KEY to your backend environment.",
            action_plan="Setup Anthropic environment variable."
        )

    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)
        
        system_prompt = """
        You are an elite, highly technical SEO Architect. 
        I am passing you a raw JSON payload representing a website's structural and performance scan.
        Your goal is to actively synthetically resolve the issues found.

        Respond with valid JSON containing exactly three keys:
        - "optimized_title": A high-converting, rewritten Meta Title directly related to their industry tags that explicitly fits within 60 characters. Fix it if it's missing or poor.
        - "optimized_meta": An aggressive, CTR-optimizing Meta Description strictly under 155 characters summarizing their offering.
        - "action_plan": A bulleted, actionable Markdown string outlining exactly to developers how to solve the items sitting inside the `issues` array of the JSON (e.g. specifically identifying their missing H1 hierarchies, load times, and missing image alt vectors).
        """

        user_prompt = f"Target Domain Scan Data:\n{json.dumps(req.scan_data, indent=2)}\n\nGenerate output JSON:"

        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.2
        )

        reply_text = response.content[0].text
        # Clean JSON markdown if Claude wraps it
        if "```json" in reply_text:
            reply_text = reply_text.split("```json")[1].split("```")[0].strip()
        elif "```" in reply_text:
            reply_text = reply_text.split("```")[1].split("```")[0].strip()

        parsed = json.loads(reply_text)
        
        return AiFixResponse(
            optimized_title=parsed.get("optimized_title", ""),
            optimized_meta=parsed.get("optimized_meta", ""),
            action_plan=parsed.get("action_plan", "")
        )

    except Exception as e:
        logger.error(f"AI Fix Failed: {e}")
        return AiFixResponse(
            optimized_title="Fix Generation Failed",
            optimized_meta="We struggled connecting to the AI provider.",
            action_plan=f"Error executing logic tree: {str(e)}"
        )

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models import SEOScan, Company
from fastapi import Depends, HTTPException
from datetime import datetime

@router.post("/company/{company_id}", response_model=ScanResult)
async def scan_and_save_company(company_id: str, db: AsyncSession = Depends(get_db)):
    """Trigger a semantic scrape on a company URL and permanently store the structural payload into the SQLite SEOScan table."""
    result = await db.execute(select(Company).filter(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    req = ScanRequest(url=company.url)
    scan_result = await scan_website(req)
    
    # Save into DB
    new_scan = SEOScan(
        company_id=company.id,
        overall_score=scan_result.seo_score,
        raw_results=scan_result.model_dump(),
        scanned_at=datetime.utcnow()
    )
    db.add(new_scan)
    await db.commit()
    await db.refresh(new_scan)
    
    return scan_result

@router.get("/company/{company_id}/latest", response_model=ScanResult)
async def get_latest_scan(company_id: str, db: AsyncSession = Depends(get_db)):
    """Pull the most recent cached synthetic scan directly from the database without invoking the headless crawler layer."""
    result = await db.execute(select(SEOScan).filter(SEOScan.company_id == company_id).order_by(SEOScan.scanned_at.desc()))
    latest_scan = result.scalars().first()
    if not latest_scan or not latest_scan.raw_results:
        # Return 404 so frontend knows to fall back to 'Not Scanned' UI state
        raise HTTPException(status_code=404, detail="No scan data found for this company")
        
    return ScanResult(**latest_scan.raw_results)
