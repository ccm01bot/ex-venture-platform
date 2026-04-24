import asyncio
from app.core.database import SessionLocal
from sqlalchemy import select
from app.models import Company, SEOScan

async def test():
    db = SessionLocal()
    result = await db.execute(select(Company))
    comps = result.scalars().all()
    for c in comps:
        scan_res = await db.execute(select(SEOScan).filter(SEOScan.company_id == c.id).order_by(SEOScan.scanned_at.desc()))
        scan = scan_res.scalars().first()
        score = scan.overall_score if scan else None
        print(f"Company {c.name} has score {score}")
    await db.close()

asyncio.run(test())
