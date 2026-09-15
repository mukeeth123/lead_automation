import asyncio
from app.core.database import SyncSessionLocal
from app.models.lead import Lead
from app.models.unified_signal import UnifiedSignalModel
from app.api.v1.leads import deep_qualify_lead, DeepQualifyRequest
from app.models.raw_event import RawEvent # Required to resolve foreign keys

async def run_batch():
    db = SyncSessionLocal()
    # Find all leads with source = freelancer that are PENDING_AI
    # Wait, the tier is on the UnifiedSignalModel
    leads = db.query(Lead).join(UnifiedSignalModel, Lead.signal_id == UnifiedSignalModel.signal_id).filter(
        UnifiedSignalModel.source == 'freelancer'
    ).limit(10).all() # Just qualify 10 for quick testing
    
    print(f"Found {len(leads)} freelancer leads. Qualifying now to update their tiers...")
    
    for idx, lead in enumerate(leads):
        req = DeepQualifyRequest(lead_id=str(lead.id))
        try:
            res = await deep_qualify_lead(req, db)
            print(f"[{idx+1}/{len(leads)}] Qualified Lead: {res.get('tier')} (Score: {res.get('score')})")
        except Exception as e:
            print(f"[{idx+1}/{len(leads)}] Error qualifying: {e}")
            
        await asyncio.sleep(2.5) # respect Groq limits
        
    db.close()

if __name__ == "__main__":
    asyncio.run(run_batch())
