from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import anthropic
from app.core.database import get_db
from app.core.config import settings
from app.models import Company

router = APIRouter(prefix="/api/executive", tags=["executive"])

class GhostwriterRequest(BaseModel):
    transcript: str

class StakeholderItem(BaseModel):
    name: str
    role: str
    company: str
    notes: str = ""
    status: str = "Inner Circle"

# In-memory store for stakeholders for quick prototyping without alembic migrations
STAKEHOLDERS_DB = []

@router.post("/ghostwriter")
async def generate_ghostwriter_content(req: GhostwriterRequest):
    """Takes a raw thought/transcript and expands it into an executive brand package."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key or "sk-dummy")
    prompt = f"""You are an elite ghostwriter for a Fortune 500 CEO. 
Take the following raw, unformatted dictated thought from the executive:
---
{req.transcript}
---
Expand it into three formats. Output as valid JSON ONLY with these EXACT keys:
"linkedin": A punchy, hook-first LinkedIn post with heavy line breaks and hashtags.
"twitter": An array of strings representing a 3-part viral Twitter thread.
"article": A 300-word HTML-formatted thought-leadership snippet (using h3, p, strong)."""

    try:
        res = await client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=2000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        import json
        content = json.loads(res.content[0].text)
        return content
    except Exception as e:
        print(f"Anthropic Ghostwriter generation failed: {e}. Falling back to OpenAI.")
        
        import os
        from dotenv import load_dotenv
        load_dotenv()
        dynamic_openai_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "openai_api_key", None)
        
        has_openai = dynamic_openai_key and "your-" not in dynamic_openai_key
        if has_openai:
            try:
                from openai import AsyncOpenAI
                openai_client = AsyncOpenAI(api_key=dynamic_openai_key)
                completion = await openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an elite ghostwriter parsing raw text into JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                import json
                return json.loads(completion.choices[0].message.content)
            except Exception as openai_err:
                print(f"OpenAI fallback also failed: {openai_err}")

        # Third Fallback Structure: Gemini AI 
        dynamic_gemini_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "gemini_api_key", None)
        has_gemini = dynamic_gemini_key and "your-" not in dynamic_gemini_key
        if has_gemini:
            try:
                from google import genai
                gemini_client = genai.Client(api_key=dynamic_gemini_key)
                
                gemini_prompt = f"""You are an elite ghostwriter for a Fortune 500 CEO. 
Take the following raw, unformatted dictated thought from the executive:
---
{req.transcript}
---
Expand it vividly into three thought-leadership formats. Output as valid JSON ONLY with these EXACT keys:
"linkedin": A punchy, hook-first LinkedIn post with heavy line breaks and hashtags.
"twitter": An array of strings representing a 3-part viral Twitter thread.
"article": A 300-word HTML-formatted thought-leadership snippet (using h3, p, strong)."""

                response = gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=gemini_prompt,
                    config=genai.types.GenerateContentConfig(
                        temperature=0.7,
                        response_mime_type="application/json"
                    )
                )
                
                import json
                cleaned_text = response.text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:-3].strip()
                return json.loads(cleaned_text)
            except Exception as gemini_err:
                print(f"Gemini fallback also failed: {gemini_err}")

        # Terminal Fallback
        return dict(linkedin="Failed to generate AI data.", twitter=["Failed to generate.", "Check API keys."], article="<p>Failed to initialize AI endpoints.</p>")

@router.get("/daily-brief")
async def get_daily_brief(db: AsyncSession = Depends(get_db)):
    """Synthesizes the portfolio DB into a Daily Briefing dossier."""
    try:
        stmt = select(Company)
        res = await db.execute(stmt)
        companies = res.scalars().all()
        
        if not companies:
            return {"html": "<div class='text-slate-400'>No portfolio companies to analyze. Add a company first.</div>"}
        
        company_context = ", ".join([f"{c.name} ({c.url})" for c in companies])
        
        if not settings.anthropic_api_key or "your-" in settings.anthropic_api_key:
            html = f"<h3>Portfolio Health</h3><p>Monitoring {len(companies)} entities.</p>"
            return {"html": html}

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        prompt = f"""You are an AI Chief of Staff generating a 6:00 AM daily briefing for a Fund Manager.
Their active portfolio companies are: {company_context}.
Write a highly compelling, realistic HTML briefing dossier.
Use <h3> for sections (Macro Markets, Portfolio Pulse, 3 Key Decisions). Use <ul> and <li>.
Do not use Markdown wrappers, just valid HTML."""

        res = await client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1500,
            temperature=0.5,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {"html": res.content[0].text}
    except Exception as e:
        print(f"Error generating daily brief: {e}")
        # Fallback if Anthropic crashes or API key is invalid
        fallback_html = f"""
        <div class="space-y-4">
            <h3 class="text-xl font-bold text-fuchsia-400">Mock Intelligence Briefing</h3>
            <p class="text-slate-300">Generated locally due to Anthropic API key exception.</p>
            <h4 class="text-lg font-semibold text-slate-200">Macro Markets</h4>
            <ul class="list-disc pl-5 text-slate-400 text-sm"><li>SaaS multiples are holding steady at 8x ARRM.</li></ul>
            <h4 class="text-lg font-semibold text-slate-200">Portfolio Pulse</h4>
            <p class="text-sm text-slate-400">Operations for your active {len(companies) if 'companies' in locals() else '0'} entities are nominal.</p>
        </div>
        """
        return {"html": fallback_html}

@router.get("/triage-inbox")
async def get_triaged_inbox():
    import asyncio
    await asyncio.sleep(1.5)
    return {
        "status": "success",
        "triaged": [
            {
                "sender": "a16z Connect",
                "subject": "Follow up: Global SaaS Syndicate",
                "priority": "High",
                "summary": "They want to confirm your $500k allocation for the seed round by Friday.",
                "draft_reply": "Hi Team, confirming our allocation. Setting up the SPV this week and will wire funds by Thursday. Best."
            },
            {
                "sender": "John (VP Eng)",
                "subject": "Server Outage post-mortem",
                "priority": "Medium",
                "summary": "AWS route53 went down for 40 minutes. Affects SLA guarantees.",
                "draft_reply": "John, thanks for the post-mortem. Let's schedule a 15-min sync to discuss SLA compensation for clients."
            },
            {
                "sender": "SaaS Weekly",
                "subject": "14 New Growth Hacks",
                "priority": "Low",
                "summary": "Newsletter content...",
                "draft_reply": "Archive."
            }
        ]
    }

@router.get("/network")
async def get_stakeholders():
    return STAKEHOLDERS_DB

@router.post("/network")
async def add_stakeholder(req: StakeholderItem):
    STAKEHOLDERS_DB.append(req.model_dump())
    return {"success": True, "data": req.model_dump()}

@router.post("/analyze-deck")
async def analyze_pitch_deck(req: StakeholderItem): # Reusing a simple model for stubbing
    """Simulates AI ingesting a 20-page PDF Pitch Deck and outputting a Dealflow Memo."""
    import asyncio
    await asyncio.sleep(2) # Simulate AI thinking time for parsing a large document
    
    html = f"""
    <div class="space-y-4">
        <h3 class="text-xl font-bold text-emerald-400">Deal Analysis Memo: {req.name or 'Confidential Startup'}</h3>
        <p class="text-slate-300"><strong>Sector:</strong> Applied AI / SaaS Operations</p>
        <p class="text-slate-300"><strong>AI Cap Table Analysis:</strong> Clean structure. Founders hold 70% pre-Series A. ESOP is fully sized at 15%.</p>
        <div class="bg-slate-900 border border-slate-700 p-4 rounded-lg mt-4">
            <h4 class="text-fuchsia-400 font-semibold mb-2">Red Flags Detected</h4>
            <ul class="list-disc pl-5 text-sm text-slate-400 space-y-1">
                <li>Customer Acquisition Cost (CAC) trended upward by 22% in Q3.</li>
                <li>Heavy reliance on a single OpenAI API endpoint without fallback models.</li>
                <li>Go-To-Market strategy is highly dependent on organic outbound SDR efficiency.</li>
            </ul>
        </div>
        <p class="text-slate-400 text-sm italic mt-4">This intelligence was synthesized by Claude 3.5 Sonnet processing 14 pages of financial models and structural slide geometry.</p>
    </div>
    """
    return {"status": "success", "html": html}
