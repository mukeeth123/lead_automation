import logging
from typing import List
from datetime import datetime, timezone
import time
import feedparser
import re
import httpx
from app.agents.base.agent import BaseSourceAgent
from app.schemas.signal import RawSignalCreate

logger = logging.getLogger(__name__)

class StartupNetworksAgent(BaseSourceAgent):
    @property
    def source_name(self) -> str:
        return "startup_networks"

    async def collect(self) -> List[RawSignalCreate]:
        signals = []
        try:
            url = "https://www.startupnetworks.co.uk/rss/5-startup-networks-all.xml/"
            headers = {"User-Agent": "Mozilla/5.0"}
            
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=15.0)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries:
                        pub_date = datetime.now(timezone.utc)
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
                            
                        desc = getattr(entry, 'description', getattr(entry, 'summary', ''))
                        clean_desc = re.sub(r'<[^>]+>', '', desc)
                        
                        signals.append(RawSignalCreate(
                            source="startup_networks",
                            external_id=f"sn-{entry.id if hasattr(entry, 'id') else entry.link}",
                            title=entry.title,
                            content=clean_desc[:1000],
                            author=getattr(entry, 'author', 'Unknown'),
                            url=entry.link,
                            published_at=pub_date
                        ))
                    
                    logger.info(f"Successfully collected {len(signals)} signals from {self.source_name} RSS")
                    
        except Exception as e:
            logger.error(f"Error collecting from {self.source_name} RSS: {e}")
            
        return signals

    async def health_check(self) -> bool:
        return len(await self.collect()) > 0
