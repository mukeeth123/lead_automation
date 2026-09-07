import httpx
from datetime import datetime, timezone
import hashlib
from app.agents.base.agent import BaseSourceAgent
from app.schemas.signal import RawSignalCreate
import logging

logger = logging.getLogger(__name__)

class UpworkAgent(BaseSourceAgent):
    @property
    def source_name(self) -> str:
        return "upwork"

    async def collect(self) -> list[RawSignalCreate]:
        signals = []
        try:
            async with httpx.AsyncClient() as client:
                query = 'site:upwork.com/freelance-jobs "developer" OR "software" OR "app" OR "api"'
                url = f"http://localhost:8080/search?q={query}&format=json"
                resp = await client.get(url, timeout=15.0)
                
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    
                    for r in results:
                        url = r.get("url", "")
                        title = r.get("title", "")
                        content = r.get("content", "")
                        
                        # Only include actual job postings, not generic directory pages
                        if "/freelance-jobs/" not in url:
                            continue
                            
                        # Try to extract budget or hourly rate from snippet if present
                        meta = {}
                        if "$" in content:
                            meta["Mentioned Pricing"] = "$" + content.split("$")[1].split(" ")[0]
                            
                        signals.append(RawSignalCreate(
                            source="upwork",
                            external_id=f"upwork-{hashlib.md5(url.encode()).hexdigest()}",
                            title=title.replace(" - Upwork", ""),
                            content=content[:1000],
                            author="Upwork Client",
                            url=url,
                            published_at=datetime.now(timezone.utc),
                            metadata_=meta
                        ))
        except Exception as e:
            logger.error(f"Upwork search error: {e}")
            
        return signals

    async def health_check(self) -> bool:
        return True
