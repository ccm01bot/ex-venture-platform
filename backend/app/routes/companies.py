from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.schemas import CompanyCreate, CompanyUpdate, CompanyResponse
from app.models import Company, SEOScan

router = APIRouter(prefix="/api/companies", tags=["companies"])

@router.get("", response_model=list[CompanyResponse])
async def list_companies(
    db: AsyncSession = Depends(get_db),
):
    """List all companies."""
    stmt = select(Company).order_by(Company.created_at.desc())
    result = await db.execute(stmt)
    companies = result.scalars().all()
    
    # Hydrate latest SEOScan score
    hydrated = []
    for c in companies:
        scan_stmt = select(SEOScan.overall_score).filter(SEOScan.company_id == c.id).order_by(SEOScan.scanned_at.desc())
        scan_res = await db.execute(scan_stmt)
        latest_score = scan_res.scalar()
        
        comp_dict = c.__dict__.copy()
        comp_dict['overall_score'] = latest_score
        hydrated.append(comp_dict)
        
    return hydrated


@router.post("", response_model=CompanyResponse)
async def create_company(
    company_data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new company."""
    company = Company(
        name=company_data.name,
        url=company_data.url,
        industry_tags=company_data.industry_tags or [],
        platform=company_data.platform,
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get company details."""
    stmt = select(Company).where(Company.id == company_id)
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return company


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    company_data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update company."""
    stmt = select(Company).where(Company.id == company_id)
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    update_data = company_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)

    await db.commit()
    await db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete company."""
    stmt = select(Company).where(Company.id == company_id)
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    await db.delete(company)
    await db.commit()
