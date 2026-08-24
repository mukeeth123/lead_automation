import logging
from typing import List
from datetime import datetime, timedelta, timezone
from app.agents.base.agent import BaseSourceAgent
from app.schemas.signal import RawSignalCreate
from .client import N8nClient
from .parser import N8nParser

logger = logging.getLogger(__name__)

class N8nAgent(BaseSourceAgent):
    @property
    def source_name(self) -> str:
        return "n8n_community"

    def __init__(self):
        self.client = N8nClient()
        self.parser = N8nParser()

    async def collect(self) -> List[RawSignalCreate]:
        signals = []
        try:
            feed_content = await self.client.fetch_feed()
            feed_data = self.client.parse_feed(feed_content)
            
            if getattr(feed_data, 'bozo', False) and not feed_data.entries:
                logger.error(f"Malformed feed data from {self.source_name}: {getattr(feed_data, 'bozo_exception', 'Unknown error')}")
                return signals

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=14)
            seen_ids = set()
            for item in feed_data.entries:
                signal = self.parser.parse_item(item)
                if signal:
                    if signal.published_at < cutoff_date:
                        continue
                    
                    if signal.external_id in seen_ids:
                        logger.debug(f"Duplicate item found: {signal.external_id}")
                        continue
                    seen_ids.add(signal.external_id)
                    signals.append(signal)
            
            logger.info(f"Successfully collected {len(signals)} signals from {self.source_name}")
            
        except Exception as e:
            logger.error(f"Error collecting from {self.source_name}: {e}")
            
        return signals

    async def health_check(self) -> bool:
        try:
            feed_content = await self.client.fetch_feed()
            feed_data = self.client.parse_feed(feed_content)
            return len(feed_data.entries) > 0
        except Exception as e:
            logger.error(f"Health check failed for {self.source_name}: {e}")
            return False
