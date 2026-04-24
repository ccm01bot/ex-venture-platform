import asyncio
from app.core.database import SessionLocal
from app.models import Company
from app.routes.website_scanner import scan_and_save_company

async def test():
    db = SessionLocal()
    try:
        res = await scan_and_save_company("a5daa9a9-69e2-42ce-9a35-6c6486f40167", db)
        print("Success:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

asyncio.run(test())
