import logging
from typing import List
from app.agents.base.agent import BaseSourceAgent
from app.schemas.signal import RawSignalCreate
from .client import StartupNetworksClient
from .parser import StartupNetworksParser

logger = logging.getLogger(__name__)

class StartupNetworksAgent(BaseSourceAgent):
    @property
    def source_name(self) -> str:
        return "startup_networks"

    def __init__(self):
        self.client = StartupNetworksClient()
        self.parser = StartupNetworksParser()

    async def collect(self) -> List[RawSignalCreate]:
        signals = []
        try:
            html_content = await self.client.fetch_page()
            signals = self.parser.parse_page(html_content)
            
            logger.info(f"Successfully collected {len(signals)} signals from {self.source_name}")
            
        except Exception as e:
            logger.error(f"Error collecting from {self.source_name}: {e}")
            
        return signals

    async def health_check(self) -> bool:
        try:
            html_content = await self.client.fetch_page()
            signals = self.parser.parse_page(html_content)
            return len(signals) > 0
        except:
            return False
