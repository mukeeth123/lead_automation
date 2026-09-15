import asyncio
import httpx
from datetime import datetime, timezone
import json
from app.core.database import SyncSessionLocal
from app.models.raw_event import RawEvent
from app.models.unified_signal import UnifiedSignalModel
from app.models.lead import Lead
from urllib.parse import quote

# Target search queries on the Bubble forum
SEARCH_QUERIES = [
    "looking for developer",
    "looking for agency",
    "need help building",
    "freelance developer",
    "hire developer"
]

async def scrape_bubble_forum(query: str):
    print(f"Searching Bubble forum for: '{query}'")
    url = f"https://forum.bubble.io/search.json?q={quote(query)}%20order:latest"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    results = []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=15.0)
            if resp.status_code == 200:
                data = resp.json()
                topics = {t["id"]: t for t in data.get("topics", [])}
                posts = data.get("posts", [])
                
                for p in posts:
                    topic_id = p.get("topic_id")
                    topic = topics.get(topic_id)
                    if not topic:
                        continue
                        
                    title = topic.get("title", "")
                    slug = topic.get("slug", "")
                    blurb = p.get("blurb", "")
                    username = p.get("username", "unknown")
                    
                    # Discourse date format: "2023-01-01T12:00:00.000Z"
                    created_at = p.get("created_at")
                    
                    item_url = f"https://forum.bubble.io/t/{slug}/{topic_id}"
                    
                    results.append({
                        "title": title,
                        "description": blurb.replace('<em>', '').replace('</em>', ''),
                        "url": item_url,
                        "author": username,
                        "date": created_at
                    })
            else:
                print(f"Error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Exception during Bubble forum search: {e}")
        
    return results

def insert_leads(leads_data):
    db = SyncSessionLocal()
    inserted_count = 0
    
    for item in leads_data:
        # Check if URL already exists
        exists = db.query(UnifiedSignalModel).filter(UnifiedSignalModel.external_url == item["url"]).first()
        if exists:
            continue
            
        try:
            # 1. RawEvent
            raw = RawEvent(
                source_name="bubble_forum",
                external_id=item["url"],
                raw_payload=item
            )
            db.add(raw)
            db.flush()
            
            # 2. UnifiedSignalModel
            import hashlib
            hash_src = f"{item['url']}_{item['title']}".encode('utf-8')
            content_hash = hashlib.md5(hash_src).hexdigest()
            
            sig = UnifiedSignalModel(
                raw_event_id=raw.id,
                source="bubble_forum",
                source_type="forum",
                external_id=item["url"],
                external_url=item["url"],
                content={"text": item["description"], "title": item["title"]},
                author={"name": item["author"]},
                content_hash=content_hash,
                metadata_={
                    "tier_label": "PENDING_AI",
                    "priority_score": 0,
                    "ai_reasoning": "Pending deep qualification"
                }
            )
            db.add(sig)
            db.flush()
            
            # 3. Lead
            lead = Lead(
                signal_id=sig.signal_id,
                person_name=item["author"], 
                status="NEW"
            )
            db.add(lead)
            db.commit()
            inserted_count += 1
            print(f"Inserted: {item['title'][:50]}...")
            
        except Exception as e:
            db.rollback()
            print(f"Error inserting item {item['url']}: {e}")
            
    db.close()
    return inserted_count

async def main():
    print("Starting Bubble Forum Scraper...")
    all_leads = []
    
    for q in SEARCH_QUERIES:
        leads = await scrape_bubble_forum(q)
        all_leads.extend(leads)
        # Be polite to the API
        await asyncio.sleep(2)
        
    print(f"\nScraped {len(all_leads)} total leads. Inserting into database...")
    
    # Deduplicate by URL before inserting
    unique_leads = {lead["url"]: lead for lead in all_leads}.values()
    
    count = insert_leads(list(unique_leads))
    print(f"\nSuccessfully inserted {count} NEW leads from Bubble Forum!")

if __name__ == "__main__":
    asyncio.run(main())
