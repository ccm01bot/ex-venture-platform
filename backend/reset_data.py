import asyncio
import os
import sys

# Add backend directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import delete
from app.core.database import AsyncSessionLocal
from app.models import SEOScan, SEOIssue, YouTubeChannel, YouTubeVideo, YouTubeSEOJob

async def reset():
    print("Connecting to database...")
    async with AsyncSessionLocal() as session:
        # Delete SEO data
        print("Cleaning SEO Issues...")
        await session.execute(delete(SEOIssue))
        print("Cleaning SEO Scans...")
        await session.execute(delete(SEOScan))
        
        # Delete YouTube Analytics & SEO Jobs data
        print("Cleaning YouTube Videos...")
        await session.execute(delete(YouTubeVideo))
        print("Cleaning YouTube SEO Jobs...")
        await session.execute(delete(YouTubeSEOJob))
        print("Cleaning YouTube Channels...")
        await session.execute(delete(YouTubeChannel))
        
        await session.commit()
        print("Commit successful.")
        
    print("SEO and YouTube Analytics data has been successfully reset for new company onboarding!")

if __name__ == "__main__":
    asyncio.run(reset())
