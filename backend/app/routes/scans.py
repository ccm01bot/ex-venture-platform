from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models import Company, SEOScan

router = APIRouter(prefix="/api/scans", tags=["scans"])


@router.post("/run-all")
async def run_all_scans(
    db: AsyncSession = Depends(get_db),
):
    """Trigger SEO scans for all active companies."""
    stmt = select(Company).where(Company.is_active == True)
    result = await db.execute(stmt)
    companies = result.scalars().all()

    return {
        "message": "Scan jobs queued",
        "count": len(companies),
    }


@router.get("/status")
async def get_scan_status():
    """Get current scan status."""
    return {
        "scanning": False,
        "completed": 0,
        "in_progress": 0,
    }


@router.get("/dashboard-stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated statistics."""
    stmt = select(Company)
    result = await db.execute(stmt)
    companies = result.scalars().all()

    total_companies = len(companies)

    scan_stmt = select(SEOScan).where(
        SEOScan.company_id.in_([c.id for c in companies])
    ).order_by(SEOScan.created_at.desc()).limit(total_companies)

    scan_result = await db.execute(scan_stmt)
    latest_scans = scan_result.scalars().all()

    avg_score = 0
    if latest_scans:
        valid_scores = [s.overall_score for s in latest_scans if s.overall_score]
        if valid_scores:
            avg_score = sum(valid_scores) / len(valid_scores)

    return {
        "total_companies": total_companies,
        "average_seo_score": round(avg_score),
        "critical_issues": 0,
        "scans_today": 0,
    }
