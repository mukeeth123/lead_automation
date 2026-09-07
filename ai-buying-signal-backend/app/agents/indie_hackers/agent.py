import logging
from typing import List
from datetime import datetime, timedelta, timezone
from app.agents.base.agent import BaseSourceAgent
from app.schemas.signal import RawSignalCreate
from .client import IndieHackersClient
from .parser import IndieHackersParser

logger = logging.getLogger(__name__)

class IndieHackersAgent(BaseSourceAgent):
    @property
    def source_name(self) -> str:
        return "indie_hackers"

    def __init__(self):
        self.client = IndieHackersClient()
        self.parser = IndieHackersParser()

    async def collect(self) -> List[RawSignalCreate]:
        signals = []
        try:
            search_queries = [
                "agency", "looking for", "developer", "outsourcing", 
                "automate", "mvp", "technical co-founder", "building"
            ]
            seen_ids = set()
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=14)
            
            import urllib.parse
            for q in search_queries:
                safe_q = urllib.parse.quote_plus(q)
                url = f"https://feed.indiehackers.world/posts.rss?q={safe_q}"
                try:
                    feed_content = await self.client.fetch_feed(url)
                    feed_data = self.client.parse_feed(feed_content)
                    
                    if getattr(feed_data, 'bozo', False) and not feed_data.entries:
                        continue
        
                    for item in feed_data.entries:
                        signal = self.parser.parse_item(item)
                        if signal:
                            if signal.published_at < cutoff_date:
                                continue
                            if signal.external_id in seen_ids:
                                continue
                            seen_ids.add(signal.external_id)
                            signals.append(signal)
                except Exception as e:
                    logger.warning(f"Error fetching IH search query {q}: {e}")
            
            logger.info(f"Successfully collected {len(signals)} signals from {self.source_name}")
            
        except Exception as e:
            logger.error(f"Error collecting from {self.source_name}: {e}")
            
        return signals

    async def health_check(self) -> bool:
        try:
            feed_content = await self.client.fetch_feed()
            feed_data = self.client.parse_feed(feed_content)
            return len(feed_data.entries) > 0
        except:
            return False
