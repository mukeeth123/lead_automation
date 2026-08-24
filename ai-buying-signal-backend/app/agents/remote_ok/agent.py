import logging
from typing import List
from datetime import datetime, timedelta, timezone
from app.agents.base.agent import BaseSourceAgent
from app.schemas.signal import RawSignalCreate
from .client import RemoteOKClient
from .parser import RemoteOKParser

logger = logging.getLogger(__name__)

class RemoteOKAgent(BaseSourceAgent):
    @property
    def source_name(self) -> str:
        return "remote_ok"

    def __init__(self):
        self.client = RemoteOKClient()
        self.parser = RemoteOKParser()

    async def collect(self) -> List[RawSignalCreate]:
        signals = []
        try:
            items = await self.client.fetch_jobs()
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=14)
            seen_ids = set()
            for item in items:
                signal = self.parser.parse_item(item)
                if signal:
                    # Filter out older signals
                    if signal.published_at.tzinfo is None:
                        signal.published_at = signal.published_at.replace(tzinfo=timezone.utc)
                        
                    if signal.published_at < cutoff_date:
                        continue
                        
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
            items = await self.client.fetch_jobs()
            return len(items) > 0
        except:
            return False
