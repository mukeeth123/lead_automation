from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.company import Company
from app.schemas.company import CompanyAnalyzeRequest, CompanyResponse, CompanyListResponse
from app.agents.company.agent import CompanyEnrichmentAgent

router = APIRouter()
agent = CompanyEnrichmentAgent()

@router.get("/", response_model=CompanyListResponse)
def list_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.created_at.desc()).all()
    # Map for response schema
    out = []
    for c in companies:
        enriched = c.enriched_data or {}
        out.append({
            "id": c.id,
            "name": c.name,
            "website": c.domain or enriched.get("website"),
            "location": enriched.get("location"),
            "industry": c.industry or enriched.get("industry"),
            "description": enriched.get("description"),
            "tech_stack": enriched.get("tech_stack", []),
            "icp_score": enriched.get("icp_score", 0),
            "icp_tier": enriched.get("icp_tier", "LOW"),
            "ai_summary": enriched.get("ai_summary"),
            "key_executives": enriched.get("key_executives", "Unknown"),
            "company_size": enriched.get("company_size", "Unknown"),
            "latest_updates": enriched.get("latest_updates", []),
            "sales_triggers": enriched.get("sales_triggers", []),
            "pain_points": enriched.get("pain_points", []),
            "pitch_recommendations": enriched.get("pitch_recommendations", []),
            "created_at": c.created_at
        })
    return {"companies": out}

@router.post("/analyze", response_model=CompanyResponse)
async def analyze_company(request: CompanyAnalyzeRequest, db: Session = Depends(get_db)):
    existing = db.query(Company).filter(Company.name.ilike(f"%{request.query}%")).first()
    if existing and existing.enriched_data and "icp_score" in existing.enriched_data:
        enriched = existing.enriched_data
        return {
            "id": existing.id,
            "name": existing.name,
            "website": existing.domain or enriched.get("website"),
            "location": enriched.get("location"),
            "industry": existing.industry or enriched.get("industry"),
            "description": enriched.get("description"),
            "tech_stack": enriched.get("tech_stack", []),
            "icp_score": enriched.get("icp_score", 0),
            "icp_tier": enriched.get("icp_tier", "LOW"),
            "ai_summary": enriched.get("ai_summary"),
            "key_executives": enriched.get("key_executives", "Unknown"),
            "company_size": enriched.get("company_size", "Unknown"),
            "latest_updates": enriched.get("latest_updates", []),
            "sales_triggers": enriched.get("sales_triggers", []),
            "pain_points": enriched.get("pain_points", []),
            "pitch_recommendations": enriched.get("pitch_recommendations", []),
            "created_at": existing.created_at
        }
        
    analysis = await agent.search_and_analyze(request.query)
    if not analysis:
        raise HTTPException(status_code=500, detail="Failed to analyze company")
        
    icp_score = analysis.get("icp_score", 0)
    icp_tier = "HOT" if icp_score >= 80 else "HIGH" if icp_score >= 60 else "LOW"
    
    enriched_data = {
        "website": analysis.get("website", ""),
        "location": analysis.get("location", ""),
        "industry": analysis.get("industry", ""),
        "description": analysis.get("description", ""),
        "tech_stack": analysis.get("tech_stack", []),
        "icp_score": icp_score,
        "icp_tier": icp_tier,
        "key_executives": analysis.get("key_executives", "Unknown"),
        "company_size": analysis.get("company_size", "Unknown"),
        "latest_updates": analysis.get("latest_updates", []),
        "sales_triggers": analysis.get("sales_triggers", []),
        "pain_points": analysis.get("pain_points", []),
        "pitch_recommendations": analysis.get("pitch_recommendations", []),
        "raw_context": analysis.get("raw_context", "")
    }
    
    if existing:
        existing.enriched_data = enriched_data
        existing.industry = analysis.get("industry", existing.industry)
        company = existing
    else:
        company = Company(
            name=analysis.get("name", request.query),
            industry=analysis.get("industry", ""),
            enriched_data=enriched_data
        )
        db.add(company)
        
    db.commit()
    db.refresh(company)
    
    return {
        "id": company.id,
        "name": company.name,
        "website": company.domain or enriched_data.get("website"),
        "location": enriched_data.get("location"),
        "industry": company.industry or enriched_data.get("industry"),
        "description": enriched_data.get("description"),
        "tech_stack": enriched_data.get("tech_stack", []),
        "icp_score": enriched_data.get("icp_score", 0),
        "icp_tier": enriched_data.get("icp_tier", "LOW"),
        "ai_summary": enriched_data.get("ai_summary"),
        "key_executives": enriched_data.get("key_executives", "Unknown"),
        "company_size": enriched_data.get("company_size", "Unknown"),
        "latest_updates": enriched_data.get("latest_updates", []),
        "sales_triggers": enriched_data.get("sales_triggers", []),
        "pain_points": enriched_data.get("pain_points", []),
        "pitch_recommendations": enriched_data.get("pitch_recommendations", []),
        "created_at": company.created_at
    }


from app.schemas.company import CompanyChatRequest, CompanyChatResponse
from app.agents.intelligence import groq_client, GROQ_MODEL


def _get_realtime_search_snippets(query: str, num_results: int = 3) -> str:
    import urllib.request
    import urllib.parse
    from bs4 import BeautifulSoup
    url = f'https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
    try:
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        snippets = []
        for a in soup.find_all('a', class_='result__snippet'):
            snippets.append(a.text.strip())
            if len(snippets) >= num_results:
                break
        return "\\n".join([f"- {s}" for s in snippets])
    except Exception:
        return ""

@router.post("/{company_id}/chat", response_model=CompanyChatResponse)
async def chat_with_company(company_id: str, request: CompanyChatRequest, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    enriched = company.enriched_data or {}
    raw_context = enriched.get("raw_context", "(No raw context available)")
    
    import json
    analysis_json = json.dumps(enriched, indent=2, default=str)
    

    realtime_snippets = _get_realtime_search_snippets(f"{company.name} {request.message}")
    
    prompt = f"""
You are a helpful AI Sales Assistant. You are answering a salesperson's questions about the company: {company.name}.

Here is the ICP Summary & Metadata we generated: 
{analysis_json}

Here is all the raw scraped data we found on them:
{raw_context}

Here are some real-time web search results for the user's specific question:
{realtime_snippets}

Answer the user's question directly and concisely based on this information. 
Use the real-time web search results if the answer is not in the original scraped context.
"""
    
    try:
        response = await groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": request.message}
            ],
            temperature=0.3
        )
        reply = response.choices[0].message.content
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
