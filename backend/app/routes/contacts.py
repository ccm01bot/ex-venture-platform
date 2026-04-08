from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.schemas import ContactCreate, ContactResponse
from app.models import Contact

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.get("", response_model=list[ContactResponse])
async def list_contacts(
    db: AsyncSession = Depends(get_db),
):
    """List all contacts."""
    stmt = select(Contact)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=ContactResponse)
async def create_contact(
    contact_data: ContactCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create new contact."""
    contact = Contact(
        first_name=contact_data.first_name,
        last_name=contact_data.last_name,
        email=contact_data.email,
        contact_type=contact_data.contact_type,
        phone=contact_data.phone,
        linkedin_url=contact_data.linkedin_url,
        twitter_handle=contact_data.twitter_handle,
        job_title=contact_data.job_title,
        organization=contact_data.organization,
        tags=contact_data.tags or [],
        notes=contact_data.notes,
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get contact details."""
    stmt = select(Contact).where(Contact.id == contact_id)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return contact


@router.post("/import")
async def import_contacts(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Import contacts from CSV."""
    return {"message": "Contacts imported", "count": 0}
