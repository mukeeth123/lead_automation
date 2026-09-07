import httpx
from datetime import datetime, timezone
from app.agents.base.agent import BaseSourceAgent
from app.schemas.signal import RawSignalCreate
import logging

logger = logging.getLogger(__name__)

class FreelancerAgent(BaseSourceAgent):
    @property
    def source_name(self) -> str:
        return "freelancer"

    async def collect(self) -> list[RawSignalCreate]:
        signals = []
        try:
            async with httpx.AsyncClient() as client:
                # Fetch more (100) since we are dropping non-US/UK
                url = "https://www.freelancer.com/api/projects/0.1/projects/active?query=developer&limit=100&compact=false"
                resp = await client.get(url, timeout=15.0)
                if resp.status_code == 200:
                    data = resp.json()
                    projects = data.get("result", {}).get("projects", [])
                    
                    for p in projects:
                        currency_code = p.get("currency", {}).get("code", "")
                        
                        # Filter strictly for USA and UK (USD, GBP)
                        if currency_code not in ["USD", "GBP"]:
                            continue
                            
                        desc = p.get("preview_description", "")
                        title = p.get("title", "")
                        seo_url = p.get("seo_url", "")
                        
                        budget = p.get("budget", {})
                        currency = p.get("currency", {})
                        b_min = budget.get("minimum", 0)
                        b_max = budget.get("maximum", 0)
                        c_sign = currency.get("sign", "$")
                        
                        meta = {
                            "Budget": f"{c_sign}{b_min} - {c_sign}{b_max}" if b_max else "Hourly/Negotiable",
                            "Type": str(p.get("type", "unknown")).title(),
                            "Bids": p.get("bid_stats", {}).get("bid_count", 0),
                            "Country": "USA" if currency_code == "USD" else "UK"
                        }
                        
                        signals.append(RawSignalCreate(
                            source="freelancer",
                            external_id=f"freelancer-{p.get('id')}",
                            title=title,
                            content=desc[:1000],
                            author=f"Client #{p.get('id')}",
                            url=f"https://www.freelancer.com/projects/{seo_url}",
                            published_at=datetime.now(timezone.utc),
                            metadata_=meta
                        ))
        except Exception as e:
            logger.error(f"Freelancer search error: {e}")
            
        return signals

    async def health_check(self) -> bool:
        return True
