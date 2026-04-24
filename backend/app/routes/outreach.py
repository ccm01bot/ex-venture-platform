from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.schemas import OutreachCampaignCreate, OutreachCampaignResponse
from app.models import OutreachCampaign
import anthropic
from pydantic import BaseModel
from app.core.config import settings
import asyncio

router = APIRouter(prefix="/api/outreach", tags=["outreach"])


@router.get("/campaigns", response_model=list[OutreachCampaignResponse])
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
):
    """List outreach campaigns."""
    stmt = select(OutreachCampaign)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/campaigns", response_model=OutreachCampaignResponse)
async def create_campaign(
    campaign_data: OutreachCampaignCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create outreach campaign."""
    campaign = OutreachCampaign(
        name=campaign_data.name,
        campaign_type=campaign_data.campaign_type,
        company_id=campaign_data.company_id,
        media_list_id=campaign_data.media_list_id,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.get("/campaigns/{campaign_id}", response_model=OutreachCampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get campaign details."""
    stmt = select(OutreachCampaign).where(OutreachCampaign.id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return campaign


@router.get("/analytics")
async def get_outreach_analytics():
    """Get outreach analytics."""
    return {
        "total_campaigns": 0,
        "active_campaigns": 0,
        "total_messages_sent": 0,
        "open_rate": 0,
        "reply_rate": 0,
    }


class LeadGenerationRequest(BaseModel):
    industry: str
    target_persona: str
    company_context: str


class LeadProfile(BaseModel):
    name: str
    title: str
    company: str
    email_guess: str
    rationale: str
    custom_intro_line: str


class LeadGenerationResponse(BaseModel):
    leads: list[LeadProfile]


@router.post("/agent/generate")
async def run_ai_outreach_agent(req: LeadGenerationRequest):
    """Continuously generate high-quality mock/predicted leads using Gemini via Infinite Stream."""
    
    async def lead_generator():
        cycle = 1
        while True:
            # We add dynamic entropy to the prompt by iterating the cycle requirement so it yields NEW specific people
            prompt = f"""
            Act as an elite Sales Development Researcher. 
            A user is trying to find high-value potential leads.
            
            Their Company Context: {req.company_context}
            Target Industry: {req.industry}
            Target Persona: {req.target_persona}
            OFFSET SEED CYCLE: {cycle} (CRITICAL: Do NOT return famous or widely known people you've already yielded. Dig deep into the sector for niche, real individuals.)
            
            Find exactly 2 REAL, ACTUAL, SPECIFIC individuals in the real world who currently hold this persona in this exact industry. Do NOT invent them. Find real executives.
            
            Output ONLY valid JSON containing EXACTLY this format, with NO markdown formatting:
            {{
              "leads": [
                {{
                  "name": "REAL First Last Name",
                  "title": "Their REAL Exact Title",
                  "company": "Their REAL Current Company",
                  "email_guess": "their.email@company.com",
                  "rationale": "1 sentence describing exactly why this specific LIVE person is a perfect buyer.",
                  "custom_intro_line": "1 personalized cold-email intro line referencing a real-world fact about their career."
                }}
              ]
            }}
            """
            
            import os
            from dotenv import load_dotenv
            load_dotenv()
            dynamic_gemini_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "gemini_api_key", None)
            
            if dynamic_gemini_key and "your-" not in dynamic_gemini_key:
                try:
                    from google import genai
                    gemini_client = genai.Client(api_key=dynamic_gemini_key)
                    
                    response = gemini_client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                        config=genai.types.GenerateContentConfig(
                            temperature=0.85, # High temperature to ensure variance
                            response_mime_type="application/json"
                        )
                    )
                    
                    cleaned_text = response.text.strip()
                    if cleaned_text.startswith("```json"):
                        cleaned_text = cleaned_text[7:-3].strip()
                    
                    # Yield raw json chunk immediately formatted to SSE or generic buffer array
                    yield cleaned_text + "\n"
                    
                except Exception as e:
                    # In case of API failure, stop streaming safely
                    print(f"Gemini Streaming Error: {e}")
                    break
            else:
                # Mock infinite fallback
                mock_json = '{{"leads": [{{"name": "Sarah Jenkins", "title": "VP Engineering", "company": "TechFlow Data", "email_guess": "sarah@techflow.io", "rationale": "Ideal Series B layout.", "custom_intro_line": "Loved the panel."}}]}}'
                yield mock_json + "\n"
            
            cycle += 1
            # Rate limit ourselves natively to prevent Google from banning the key due to aggressive loops
            await asyncio.sleep(4)

    return StreamingResponse(lead_generator(), media_type="application/x-ndjson")
