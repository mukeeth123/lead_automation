import asyncio
import httpx
import uuid
from datetime import datetime, timezone
import urllib.parse
from app.core.database import SyncSessionLocal
from app.models.lead import Lead
from app.models.unified_signal import UnifiedSignalModel
from app.models.raw_event import RawEvent
from app.graph.nodes.qualification import static_pre_filter

queries = ["web development", "Voice ai", "AI enterprise platform", "mobile applications"]

# Allowed regions as strings to check against snippet/title if location API data is missing
allowed_regions = ["north america", "europe", "arab", "usa", "uk", "uae", "dubai", "canada", "germany", "france"]

async def seed_leads():
    db = SyncSessionLocal()
    campaign_id = "00000000-0000-0000-0000-000000000000" # fallback id or we can fetch a valid campaign
    
    # Try to get the first campaign to tie these leads to
    from app.models.campaign import Campaign
    camp = db.query(Campaign).first()
    if camp:
        campaign_id = str(camp.id)
    
    saved_count = 0

    async def save_lead(title, content, url, source):
        nonlocal saved_count
        if saved_count >= 100: # 50 from each source roughly
            return
            
        passed, _ = static_pre_filter(content)
        if not passed:
            return
            
        raw = RawEvent(
            source_name=source,
            external_id=str(uuid.uuid4()),
            raw_payload={"url": url, "title": title}
        )
        db.add(raw)
        db.flush()
        
        signal = UnifiedSignalModel(
            source=source,
            source_type="web",
            external_id=url[:255],
            external_url=url[:255],
            campaign_id=campaign_id,
            content={"text": content[:250] + "..." if len(content) > 250 else content},
            raw_event_id=raw.id,
            metadata_={
                "priority_score": 50,
                "tier_label": "PENDING_AI",
                "ai_summary": content[:250] + "..." if len(content) > 250 else content
            },
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
        print(f"[{saved_count}/100] Saved lead from {source}: {title[:30]}...")

    async with httpx.AsyncClient() as client:
        # Freelancer
        for q in queries:
            print(f"Fetching Freelancer for: {q}")
            try:
                base_kw = urllib.parse.quote(q)
                resp = await client.get(f"https://www.freelancer.com/api/projects/0.1/projects/active/?query={base_kw}&limit=50", timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    projects = data.get('result', {}).get('projects', [])
                    for p in projects:
                        title = p.get("title", "")
                        desc = p.get("preview_description", "")
                        url = f"https://www.freelancer.com/projects/{p.get('seo_url')}"
                        await save_lead(title, desc, url, "Freelancer")
            except Exception as e:
                print(f"Error fetching freelancer for {q}: {e}")

        # PeoplePerHour (via DDG)
        from ddgs import DDGS
        for q in queries:
            print(f"Fetching PeoplePerHour for: {q}")
            try:
                with DDGS() as ddgs:
                    ddg_q = f'{q} site:peopleperhour.com/freelance-jobs'
                    results = list(ddgs.text(ddg_q, max_results=30))
                    for r in results:
                        await save_lead(r.get("title", ""), r.get("body", ""), r.get("href", ""), "PeoplePerHour")
            except Exception as e:
                print(f"Error fetching PPH for {q}: {e}")
                
    db.close()
    print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_leads())
