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
                    # Filter out older signals
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
        except:
            return False
