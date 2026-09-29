import asyncio
import sys
import os
import uuid
import time
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SyncSessionLocal
from app.models.lead import Lead
from app.models.unified_signal import UnifiedSignalModel
from app.models.raw_event import RawEvent
from app.models.service_catalog import CompanyService
from sqlalchemy import select

from app.agents.reddit.agent import RedditAgent
from app.agents.github.agent import GithubAgent
from app.agents.hackernews.agent import HackerNewsAgent
from app.agents.indie_hackers.agent import IndieHackersAgent
from app.agents.freelancer.agent import FreelancerAgent
from app.agents.peopleperhour.agent import PeoplePerHourAgent
from app.agents.bubble_forum.agent import BubbleForumAgent

from app.agents.intelligence import deep_qualify_post

async def fetch_and_process():
    db = SyncSessionLocal()
    
    # 1. Fetch Service Catalog
    services_result = db.execute(select(CompanyService))
    all_services = services_result.scalars().all()
    company_services = [s.name for s in all_services if not s.is_excluded]
    excluded_services = [s.name for s in all_services if s.is_excluded]

    agents = [
        RedditAgent(),
        GithubAgent(),
        HackerNewsAgent(),
        IndieHackersAgent(),
        FreelancerAgent(),
        PeoplePerHourAgent(),
        BubbleForumAgent()
    ]
    
    total_new = 0
    
    for agent in agents:
        source_name = getattr(agent, 'source_name', agent.__class__.__name__.replace('Agent', '').lower())
        print(f"\n--- Fetching from {source_name} ---")
        try:
            signals = await agent.collect()
            print(f"Collected {len(signals)} raw signals from {source_name}.")
            
            for sig in signals:
                # Check if exists
                existing = db.execute(select(UnifiedSignalModel).where(UnifiedSignalModel.external_id == sig.external_id)).scalars().first()
                if existing:
                    continue
                
                # Qualify
                qual_result = await deep_qualify_post(
                    content=sig.content,
                    title=sig.title,
                    source=sig.source,
                    campaign_name="Global Fetch",
                    company_services=company_services,
                    excluded_services=excluded_services
                )
                
                if "error" in qual_result:
                    continue
                    
                is_active_request = qual_result.get("is_active_request", False)
                looking_ext = qual_result.get("is_looking_for_external_provider", False)
                service_match = qual_result.get("service_match", False)
                service_match_confidence = float(qual_result.get("service_match_confidence") or 0.0)
                llm_tier = qual_result.get("lead_status", "REJECTED")
                reasoning = qual_result.get("ai_summary") or qual_result.get("matched_company_service") or "Unknown"
                
                # Strict matching rule
                if is_active_request and looking_ext and service_match and service_match_confidence >= 0.70:
                    score = int(70 + (service_match_confidence * 30))
                    score = min(score, 100)
                    tier = llm_tier if llm_tier in ["HOT", "WARM", "QUALIFIED"] else "HOT"
                elif is_active_request and looking_ext and service_match and service_match_confidence >= 0.50:
                    score = int(40 + (service_match_confidence * 40))
                    tier = "WARM"
                else:
                    score = 0
                    tier = "REJECTED"
                
                # Only save if WARM or HOT
                if tier == "REJECTED":
                    continue
                    
                # Save Raw Event
                raw = RawEvent(
                    source_name=sig.source,
                    external_id=sig.external_id,
                    raw_payload={"url": sig.url}
                )
                db.add(raw)
                db.flush()
                
                # Save Unified Signal
                signal_model = UnifiedSignalModel(
                    source=sig.source,
                    source_type="web",
                    external_id=sig.external_id,
                    external_url=sig.url,
                    content={"title": sig.title, "text": sig.content},
                    raw_event_id=raw.id,
                    metadata_={
                        "priority_score": score,
                        "tier_label": tier,
                        "ai_summary": reasoning,
                        "deep_qualification_result": qual_result
                    },
                    content_hash=str(uuid.uuid4())
                )
                db.add(signal_model)
                db.flush()
                
                # Save Lead
                lead = Lead(
                    signal_id=signal_model.signal_id,
                    person_name=sig.author,
                    status="NEW"
                )
                db.add(lead)
                db.commit()
                
                total_new += 1
                print(f" -> Saved HOT/WARM lead: {sig.title[:40]}...")
                
                # Rate limit safety for groq
                await asyncio.sleep(2.5)
                
        except Exception as e:
            print(f"Error fetching from {source_name}: {e}")
            import traceback
            traceback.print_exc()
            
    print(f"\nDone! Added {total_new} new qualified leads to the database.")
    db.close()

if __name__ == "__main__":
    asyncio.run(fetch_and_process())
