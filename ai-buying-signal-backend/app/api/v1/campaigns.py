from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import uuid
from arq import create_pool
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.redis import get_redis_settings
from app.core.database import get_db
from app.models.campaign import Campaign
from app.models.lead import Lead
from app.models.unified_signal import UnifiedSignalModel

router = APIRouter()

class DiscoveryResponse(BaseModel):
    job_id: str
    status: str

class CampaignCreate(BaseModel):
    name: str
    service_description: str
    target_industry: str | None = None
    target_geography: str | None = None

@router.get("/")
def get_campaigns(db: Session = Depends(get_db)):
    result = db.execute(select(Campaign).order_by(Campaign.created_at.desc()))
    campaigns = result.scalars().all()
    return {"campaigns": campaigns}

@router.post("/")
def create_campaign(req: CampaignCreate, db: Session = Depends(get_db)):
    campaign = Campaign(
        name=req.name,
        service_description=req.service_description,
        target_industry=req.target_industry,
        target_geography=req.target_geography
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign

from fastapi import BackgroundTasks
import asyncio
from app.graph.discovery_graph import discovery_graph

def run_sync_discovery(campaign_id: str):
    from app.core.database import SyncSessionLocal
    from app.models.campaign import Campaign
    from app.models.lead import Lead
    from app.models.unified_signal import UnifiedSignalModel
    from app.models.raw_event import RawEvent
    
    db = SyncSessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            print("Campaign not found")
            return
            
        initial_state = {
            "campaign_name": campaign.name,
            "industry": campaign.target_industry or "Any",
            "service": campaign.service_description or "Any",
            "icp": campaign.target_geography or "Any",
            "keywords": [],
            "search_queries": [
                f"need an {campaign.name} company",
                f"looking for an {campaign.name} partner",
                "who can build AI solutions for us"
            ],
            "discovered_urls": [],
            "deduplicated_urls": [],
            "current_url_index": 0,
            "current_url_data": None,
            "selected_crawler": "",
            "extraction_failed": False,
            "retry_count": 0,
            "extracted_content": None,
            "is_qualified": False,
            "tier": None,
            "score": 0,
            "qualification_breakdown": [],
            "enriched_company_info": None,
            "saved_leads": [],
            "errors": []
        }
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        final_state = loop.run_until_complete(discovery_graph.ainvoke(initial_state))
        loop.close()
        
        # Save to DB
        for l_data in final_state.get("saved_leads", []):
            raw = RawEvent(
                source_name=l_data.get("source", "Unknown"),
                external_id=str(uuid.uuid4()),
                raw_payload={"url": l_data.get("url")}
            )
            db.add(raw)
            db.flush()
            
            signal = UnifiedSignalModel(
                source=l_data.get("source", "Unknown"),
                source_type="web",
                external_id=l_data.get("url", "")[:255],
                external_url=l_data.get("url", "")[:255],
                campaign_id=campaign_id,
                content={"text": l_data.get("aiSummary")},
                raw_event_id=raw.id,
                metadata_={
                    "priority_score": l_data.get("intentScore", 0),
                    "tier_label": l_data.get("tierLabel", "LOW"),
                    "ai_summary": l_data.get("aiSummary", "")
                },
                content_hash=str(uuid.uuid4())
            )
            db.add(signal)
            db.flush()
            
            lead = Lead(
                signal_id=signal.signal_id,
                person_name=l_data.get("author", "Unknown"),
                status="NEW"
            )
            db.add(lead)
            
        db.commit()
        print(f"Successfully saved {len(final_state.get('saved_leads', []))} leads to DB.")
    except Exception as e:
        print(f"Background discovery failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

@router.post("/{campaign_id}/discover", response_model=DiscoveryResponse)
async def trigger_discovery(campaign_id: str, background_tasks: BackgroundTasks):
    """
    Trigger a background discovery job without ARQ/Redis for MVP mode.
    """
    try:
        job_id = str(uuid.uuid4())
        
        # Run it directly in a FastAPI background task
        background_tasks.add_task(run_sync_discovery, campaign_id)
        
        return DiscoveryResponse(job_id=job_id, status="QUEUED_LOCALLY")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_all_sync_discovery():
    from app.core.database import SyncSessionLocal
    from app.models.campaign import Campaign
    db = SyncSessionLocal()
    try:
        campaigns = db.query(Campaign).all()
        # Collect IDs to avoid keeping session open during long running tasks
        campaign_ids = [str(c.id) for c in campaigns]
    finally:
        db.close()
        
    for cid in campaign_ids:
        print(f"Starting discovery for campaign {cid}")
        run_sync_discovery(cid)
        import time
        time.sleep(2) # Brief pause between campaigns to avoid rate limit spikes

@router.post("/discover-all", response_model=DiscoveryResponse)
async def trigger_all_discovery(background_tasks: BackgroundTasks):
    """
    Trigger discovery for all campaigns sequentially.
    """
    try:
        job_id = str(uuid.uuid4())
        background_tasks.add_task(run_all_sync_discovery)
        return DiscoveryResponse(job_id=job_id, status="QUEUED_LOCALLY")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{campaign_id}/leads")
def get_campaign_leads(campaign_id: str, db: Session = Depends(get_db)):
    """
    Get all leads associated with a specific campaign.
    """
    # For now, we will just return all leads joined with their signals
    # In a real app, Leads would have a campaign_id foreign key, but right now our leads table
    # doesn't have a campaign_id directly, or does it? Wait, let's check Lead model.
    # Actually, Leads don't have campaign_id in the current schema. We'll just return all leads 
    # to simulate a unified dashboard for this single-tenant app.
    result = db.execute(select(Lead).order_by(Lead.created_at.desc()))
    leads = result.scalars().all()
    
    output = []
    for lead in leads:
        # Fetch associated signal
        sig_result = db.execute(select(UnifiedSignalModel).where(UnifiedSignalModel.signal_id == lead.signal_id))
        signal = sig_result.scalars().first()
        
        output.append({
            "id": lead.id,
            "signal_id": lead.signal_id,
            "person_name": lead.person_name,
            "job_title": lead.job_title,
            "email": lead.email,
            "linkedin_url": lead.linkedin_url,
            "status": lead.status,
            "enrichment_data": lead.enrichment_data,
            "created_at": lead.created_at,
            "signal_content": signal.content if signal else None,
            "signal_url": signal.external_url if signal else None,
            "source": signal.source if signal else None,
            "ai_metadata": signal.metadata_ if signal else {}
        })
    return {"leads": output}
