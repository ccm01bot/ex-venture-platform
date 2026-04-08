from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.schemas import OutreachCampaignCreate, OutreachCampaignResponse
from app.models import OutreachCampaign
import anthropic
from pydantic import BaseModel
from app.core.config import settings

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


@router.post("/agent/generate", response_model=LeadGenerationResponse)
async def run_ai_outreach_agent(req: LeadGenerationRequest):
    """Generate high-quality mock/predicted leads using Anthropic acting as a seasoned SDR."""
    
    if not settings.anthropic_api_key or "your-" in settings.anthropic_api_key:
        # Fallback offline mock response
        return LeadGenerationResponse(leads=[
            LeadProfile(
                name="Sarah Jenkins", 
                title="VP Engineering", 
                company="TechFlow Data", 
                email_guess="sarah.j@techflow.io", 
                rationale="Ideal buyer profile for infrastructure tooling in Series B scaleups.", 
                custom_intro_line="Saw your recent panel on navigating microservices latency—brilliant points on Redis bottlenecks."
            ),
            LeadProfile(
                name="Marcus Vance", 
                title="Head of Growth", 
                company="Apex Solar", 
                email_guess="marcus@apexsolar.com", 
                rationale="Matches the clean-tech growth trajectory looking for platform scale.", 
                custom_intro_line="Loved the recent Series A announcement for Apex; scaling sales ops must be a massive priority right now."
            )
        ])

    anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    
    prompt = f"""
    Act as a brilliant Sales Development Representative (SDR) and lead researcher. 
    A user is trying to find high-value potential leads to reach out to.
    
    Their Company Context: {req.company_context}
    Target Industry: {req.industry}
    Target Persona: {req.target_persona}
    
    I need you to "brainstorm/predict" exactly 4 hyper-realistic, highly-qualified lead profiles that this user should target. For each lead, invent a realistic persona that perfectly aligns with realistic market dynamics.
    
    Output ONLY valid JSON containing EXACTLY this format, with NO markdown formatting:
    {{
      "leads": [
        {{
          "name": "First Last",
          "title": "Exact Title",
          "company": "Fictional but realistic company name",
          "email_guess": "first.last@company.com",
          "rationale": "1 sentence describing exactly why this specific profile is a perfect buyer.",
          "custom_intro_line": "1 incredibly personalized cold-email intro line (the 'hook') that proves we researched them."
        }}
      ]
    }}
    """
    
    try:
        response = await anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1500,
            temperature=0.8,
            messages=[{"role": "user", "content": prompt}]
        )
        import json
        import re
        content = response.content[0].text.strip()
        # Clean any accidental markdown wrap
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'^```\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        data = json.loads(content)
        return LeadGenerationResponse(**data)
    except Exception as e:
        # Graceful fallback logic
        return LeadGenerationResponse(leads=[])
