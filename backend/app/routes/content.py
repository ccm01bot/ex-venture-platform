from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.schemas import ContentItemCreate, ContentItemResponse
from app.models import Company, ContentItem
from app.tasks.content_tasks import generate_article

router = APIRouter(prefix="/api/content", tags=["content"])


@router.get("", response_model=list[ContentItemResponse])
async def list_content(
    company_id: UUID = None,
    db: AsyncSession = Depends(get_db),
):
    """List content items."""
    if company_id:
        stmt = select(ContentItem).where(ContentItem.company_id == company_id)
    else:
        stmt = select(ContentItem)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=ContentItemResponse)
async def generate_content(
    company_id: UUID,
    content_data: ContentItemCreate,
    db: AsyncSession = Depends(get_db),
):
    """Generate new content item."""
    stmt = select(Company).where(Company.id == company_id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    content = ContentItem(
        company_id=company_id,
        platform=content_data.platform,
        tone=content_data.tone,
        topic=content_data.topic,
        target_length=content_data.target_length,
        video_source_url=content_data.video_source_url,
        image_style=content_data.image_style,
        status="draft",
    )
    db.add(content)
    await db.commit()
    await db.refresh(content)

    # Trigger async code generation
    generate_article.delay(str(content.id))

    return content


@router.get("/{content_id}", response_model=ContentItemResponse)
async def get_content(
    content_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get content item details."""
    stmt = select(ContentItem).where(ContentItem.id == content_id)
    result = await db.execute(stmt)
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return content


@router.post("/{content_id}/publish", response_model=ContentItemResponse)
async def publish_content(
    content_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Publish content item."""
    stmt = select(ContentItem).where(ContentItem.id == content_id)
    result = await db.execute(stmt)
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    from datetime import datetime
    content.status = "published"
    content.published_at = datetime.utcnow()

    await db.commit()
    await db.refresh(content)
    return content


@router.post("/{content_id}/upload-photos")
async def upload_photos(
    content_id: UUID,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload photos for content."""
    stmt = select(ContentItem).where(ContentItem.id == content_id)
    result = await db.execute(stmt)
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    photo_urls = [f"https://s3.example.com/{file.filename}" for file in files]
    content.user_photos = photo_urls

    await db.commit()
    await db.refresh(content)

    return {"message": "Photos uploaded", "urls": photo_urls}
