import httpx
from datetime import datetime, timezone
import time
from app.agents.base.agent import BaseSourceAgent
from app.schemas.signal import RawSignalCreate
import logging

logger = logging.getLogger(__name__)

class HNFreelanceAgent(BaseSourceAgent):
    @property
    def source_name(self) -> str:
        return "hn_freelance"

    async def collect(self) -> list[RawSignalCreate]:
        signals = []
        try:
            async with httpx.AsyncClient() as client:
                # 1. Find the latest "Seeking freelancer" thread
                thread_query = '"Ask HN: Freelancer? Seeking freelancer?"'
                search_url = f"https://hn.algolia.com/api/v1/search_by_date?query={thread_query}&tags=story"
                
                resp = await client.get(search_url, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    hits = data.get("hits", [])
                    if not hits:
                        return []
                        
                    # Get the most recent thread ID
                    latest_thread_id = hits[0].get("objectID")
                    
                    # 2. Fetch the comments for this thread
                    comments_url = f"https://hn.algolia.com/api/v1/search?tags=comment,story_{latest_thread_id}&hitsPerPage=100"
                    comments_resp = await client.get(comments_url, timeout=10.0)
                    
                    if comments_resp.status_code == 200:
                        comments_data = comments_resp.json()
                        for item in comments_data.get("hits", []):
                            content = item.get("comment_text", "")
                            if not content:
                                continue
                                
                            # Strict filtering: We ONLY want founders seeking freelancers,
                            # NOT freelancers posting their own resumes.
                            upper_content = content.upper()
                            if "SEEKING FREELANCER" not in upper_content or "SEEKING WORK" in upper_content:
                                continue
                                
                            # Convert Algolia created_at_i (timestamp) to datetime
                            created_ts = item.get("created_at_i")
                            if created_ts:
                                pub_date = datetime.fromtimestamp(created_ts, timezone.utc)
                            else:
                                pub_date = datetime.now(timezone.utc)
                                
                            signals.append(RawSignalCreate(
                                source="hn_freelance",
                                external_id=f"hn-{item.get('objectID')}",
                                title="Hacker News Freelance Opportunity",
                                content=content[:1000],
                                author=item.get("author", "Unknown"),
                                url=f"https://news.ycombinator.com/item?id={item.get('objectID')}",
                                published_at=pub_date
                            ))
        except Exception as e:
            logger.error(f"HN Freelance search error: {e}")
            
        return signals

    async def health_check(self) -> bool:
        return True
