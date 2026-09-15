import re

file_path = "app/api/v1/leads.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Fix the corrupted analyze_lead function
corrupt_pattern = r"""@router\.post\("/leads/analyze"\)
async def analyze_lead\(req: AnalyzeRequest\):
                "url": req\.url
            }
        \)
        final_state = await app_graph\.ainvoke\(initial_state\)"""

fixed_analyze = """@router.post("/leads/analyze")
async def analyze_lead(req: AnalyzeRequest):
    from app.graph.graph import app_graph
    from app.graph.state import AgentState
    
    global _last_request_time
    async with _analyze_semaphore:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < 2.5:
            await asyncio.sleep(2.5 - elapsed)
        _last_request_time = time.time()
        
        initial_state = AgentState(
            raw_signal={
                "title": req.title, 
                "content": req.content,
                "author": req.author,
                "source": req.source,
                "url": req.url
            }
        )
        final_state = await app_graph.ainvoke(initial_state)"""

content = content.replace(
    '@router.post("/leads/analyze")\nasync def analyze_lead(req: AnalyzeRequest):\n                "url": req.url\n            }\n        )\n        final_state = await app_graph.ainvoke(initial_state)',
    fixed_analyze
)

# 2. Replace get_leads
start_marker = '@router.get("/leads")\nasync def get_leads():'
end_marker = 'class AnalyzeRequest(BaseModel):'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_get_leads = """from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
from app.models.lead import Lead
from app.models.unified_signal import UnifiedSignal

@router.get("/leads")
def get_leads(db: Session = Depends(get_db)):
    \"\"\"Return all leads from the database.\"\"\"
    result = db.execute(select(Lead).order_by(Lead.created_at.desc()).limit(100))
    db_leads = result.scalars().all()
    
    formatted_leads = []
    for lead in db_leads:
        sig_result = db.execute(select(UnifiedSignal).where(UnifiedSignal.signal_id == lead.signal_id))
        signal = sig_result.scalars().first()
        
        meta = signal.ai_metadata if signal and signal.ai_metadata else {}
        
        formatted_leads.append({
            "id": lead.id,
            "signal_id": lead.signal_id,
            "author": lead.person_name or "Unknown",
            "industry": meta.get("industry", "Unknown"),
            "source": signal.source if signal else "Unknown",
            "intentScore": meta.get("priority_score", 0),
            "tierLabel": meta.get("tier_label", "LOW"),
            "aiSummary": meta.get("ai_summary", "Unknown"),
            "publishedDate": signal.published_at.isoformat() if signal and signal.published_at else lead.created_at.isoformat(),
            "originalUrl": signal.url if signal else "",
            "company": lead.company_id or "Unknown",
            "email": lead.email,
            "linkedin_url": lead.linkedin_url,
            "status": lead.status,
            "contactVerification": lead.enrichment_status
        })
        
    return {
        "stats": {
            "processingDelay": "12ms",
            "activeCollectors": 0,
            "totalSignalsScanned": len(formatted_leads)
        },
        "leads": formatted_leads
    }

"""
    content = content[:start_idx] + new_get_leads + content[end_idx:]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Done fixing leads.py")
