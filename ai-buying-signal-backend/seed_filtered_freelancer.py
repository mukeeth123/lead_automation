import asyncio
import uuid
from datetime import datetime, timezone
from app.core.database import SyncSessionLocal
from app.models.lead import Lead
from app.models.unified_signal import UnifiedSignalModel
from app.models.raw_event import RawEvent
from app.agents.freelancer.agent import FreelancerAgent
from app.models.campaign import Campaign

async def seed_filtered_freelancer():
    print("Fetching filtered freelancer leads...")
    agent = FreelancerAgent()
    signals = await agent.collect()
    print(f"Fetched {len(signals)} leads with filtered locations.")

    db = SyncSessionLocal()
    campaign_id = "00000000-0000-0000-0000-000000000000"
    camp = db.query(Campaign).first()
    if camp:
        campaign_id = str(camp.id)

    saved_count = 0
    for s in signals:
        if saved_count >= 50:
            break
            
        raw = RawEvent(
            source_name="Freelancer.com",
            external_id=str(uuid.uuid4()),
            raw_payload={"url": s.url, "title": s.title, "metadata": s.metadata_}
        )
        db.add(raw)
        db.flush()
        
        signal = UnifiedSignalModel(
            source="Freelancer.com",
            source_type="web",
            external_id=s.url[:255],
            external_url=s.url[:255],
            campaign_id=campaign_id,
            content={"text": s.title, "description": s.content},
            raw_event_id=raw.id,
            metadata_=s.metadata_,
            content_hash=str(uuid.uuid4()),
            published_at=datetime.now(timezone.utc)
        )
        db.add(signal)
        db.flush()
        
        lead = Lead(
            signal_id=signal.signal_id,
            person_name="Unknown",
            status="NEW"
        )
        db.add(lead)
        db.commit()
        saved_count += 1
        print(f"[{saved_count}] Saved Freelancer.com lead: {s.title[:50]}...")

    db.close()
    print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_filtered_freelancer())
