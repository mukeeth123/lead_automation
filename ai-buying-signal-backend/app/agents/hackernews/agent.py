import logging
from typing import List
from datetime import datetime, timedelta, timezone
from app.agents.base.agent import BaseSourceAgent
from app.schemas.signal import RawSignalCreate
from .client import HackerNewsClient
from .parser import HackerNewsParser

logger = logging.getLogger(__name__)

class HackerNewsAgent(BaseSourceAgent):
    @property
    def source_name(self) -> str:
        return "hackernews"

    def __init__(self):
        self.client = HackerNewsClient()
        self.parser = HackerNewsParser()

    async def collect(self) -> List[RawSignalCreate]:
        signals = []
        try:
            # Get latest 50 Ask HN stories
            story_ids = await self.client.fetch_ask_stories(limit=50)
            
            # Fetch full items in parallel
            items = await self.client.fetch_items(story_ids)
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=14)
            seen_ids = set()
            
            for item in items:
                signal = self.parser.parse_item(item)
                if signal:
                    # Filter out old signals
                    if signal.published_at < cutoff_date:
                        continue
                        
                    # Deduplicate
                    if signal.external_id in seen_ids:
                        continue
                    seen_ids.add(signal.external_id)
                    signals.append(signal)
            
            logger.info(f"Successfully collected {len(signals)} signals from {self.source_name}")
            
        except Exception as e:
            logger.error(f"Error collecting from {self.source_name}: {e}")
            
        return signals

    async def health_check(self) -> bool:
        try:
            # Just do a quick check to see if we can reach the API
            await self.client.fetch_ask_stories(limit=1)
            return True
        except Exception as e:
            logger.error(f"Health check failed for {self.source_name}: {e}")
            return False
