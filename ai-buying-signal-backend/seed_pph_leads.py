import asyncio
import urllib.parse
import uuid
from datetime import datetime, timezone
from app.core.database import SyncSessionLocal
from app.models.lead import Lead
from app.models.unified_signal import UnifiedSignalModel
from app.models.raw_event import RawEvent
from app.graph.nodes.qualification import static_pre_filter
from playwright.async_api import async_playwright

queries = ["AI agents", "Voice AI", "enterprise development platform", "building agents", "workflow automations"]

async def seed_pph():
    db = SyncSessionLocal()
    campaign_id = "00000000-0000-0000-0000-000000000000"
    from app.models.campaign import Campaign
    camp = db.query(Campaign).first()
    if camp:
        campaign_id = str(camp.id)
    
    saved_count = 0

    def save_lead(title, url):
        nonlocal saved_count
        if saved_count >= 50:
            return
            
        raw = RawEvent(
            source_name="PeoplePerHour",
            external_id=str(uuid.uuid4()),
            raw_payload={"url": url, "title": title}
        )
        db.add(raw)
        db.flush()
        
        signal = UnifiedSignalModel(
            source="PeoplePerHour",
            source_type="web",
            external_id=url[:255],
            external_url=url[:255],
            campaign_id=campaign_id,
            content={"text": title},
            raw_event_id=raw.id,
            metadata_={
                "priority_score": 50,
                "tier_label": "PENDING_AI",
                "ai_summary": title
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
        print(f"[{saved_count}/50] Saved PPH lead: {title[:30]}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        for q in queries:
            if saved_count >= 50:
                break
            print(f"Fetching PPH for: {q}")
            try:
                page = await context.new_page()
                query = urllib.parse.quote(q)
                url = f"https://www.peopleperhour.com/freelance-jobs?q={query}"
                await page.goto(url, wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)
                
                links = await page.locator('a[href*="/freelance-jobs/"]').element_handles()
                seen_pph = set()
                for link in links:
                    if saved_count >= 50:
                        break
                    href = await link.get_attribute("href")
                    text = await link.inner_text()
                    
                    if href and "-" in href and href.count("-") > 2:
                        href = href if href.startswith("http") else f"https://www.peopleperhour.com{href}"
                        if href not in seen_pph:
                            seen_pph.add(href)
                            save_lead(text.strip(), href)
                await page.close()
            except Exception as e:
                print(f"Error fetching PPH for {q}: {e}")
                
        await browser.close()
                
    db.close()
    print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_pph())
