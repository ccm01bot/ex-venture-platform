from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models import Company, SEOScan
from datetime import datetime, timedelta

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
    critical_issues = 0
    if latest_scans:
        valid_scores = [s.overall_score for s in latest_scans if s.overall_score]
        if valid_scores:
            avg_score = sum(valid_scores) / len(valid_scores)
            
        for s in latest_scans:
            if s.raw_results and isinstance(s.raw_results, dict):
                issues = s.raw_results.get("issues", [])
                critical_issues += sum(1 for i in issues if isinstance(i, dict) and i.get("severity") == "critical")

    # Scans today
    start_of_today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_stmt = select(func.count(SEOScan.id)).where(SEOScan.scanned_at >= start_of_today)
    today_result = await db.execute(today_stmt)
    scans_today = today_result.scalar() or 0

    return {
        "total_companies": total_companies,
        "average_seo_score": round(avg_score),
        "critical_issues": critical_issues,
        "scans_today": scans_today,
    }


@router.get("/report/weekly")
async def get_weekly_seo_digest(
    weeks_ago: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed SEO scan arrays aggregated by historical week offset."""
    now = datetime.utcnow()
    # E.g., if weeks_ago=0, upper=now, lower=now - 7 days.
    # if weeks_ago=1, upper=now - 7 days, lower=now - 14 days.
    end_date = now - timedelta(days=7 * weeks_ago)
    start_date = end_date - timedelta(days=7)

    # Note: We do a simple query extracting all scans in this boundary, 
    # but only keep the latest per company_id using a dict
    stmt = select(SEOScan, Company).join(Company, SEOScan.company_id == Company.id).where(
        SEOScan.scanned_at >= start_date,
        SEOScan.scanned_at <= end_date
    ).order_by(SEOScan.scanned_at.asc())
    
    result = await db.execute(stmt)
    rows = result.all()
    
    latest_weekly_scans = {}
    for scan, company in rows:
        latest_weekly_scans[company.id] = {
            "company_name": company.name,
            "url": company.url,
            "scanned_at": scan.scanned_at.isoformat() if scan.scanned_at else None,
            "raw_results": scan.raw_results
        }
    
    # Format into flat array for frontend autoTable easily
    formatted = []
    for cid, data in latest_weekly_scans.items():
        r = data["raw_results"] or {}
        passes_len = len(r.get("passes", []))
        issues_len = len(r.get("issues", []))
        status_code = r.get("status_code", 0)
        
        formatted.append({
            "Company": data["company_name"],
            "URL": data["url"],
            "Score": r.get("seo_score", 0),
            "Load Time": f"{r.get('load_time_ms', 0)}ms",
            "Word Count": r.get("word_count", 0),
            "Status": f"HTTP {status_code}",
            "Issues": issues_len,
            "Checks Passed": passes_len,
            "HTTPS": "Yes" if r.get("has_ssl") else "No"
        })
        
    return {
        "week_start": start_date.strftime("%Y-%m-%d"),
        "week_end": end_date.strftime("%Y-%m-%d"),
        "scans": formatted
    }
