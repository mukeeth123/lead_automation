import httpx
from datetime import datetime, timezone
from app.agents.base.agent import BaseSourceAgent
from app.schemas.signal import RawSignalCreate
import logging

logger = logging.getLogger(__name__)

# Target regions: North America, UK, Australia, Arab Gulf countries
ALLOWED_CURRENCIES = {
    "USD": "USA",
    "GBP": "United Kingdom",
    "EUR": "Europe",
    "AED": "UAE",
    "SAR": "Saudi Arabia",
    "QAR": "Qatar",
    "KWD": "Kuwait",
    "BHD": "Bahrain",
    "OMR": "Oman",
}

# Explicitly blocked currencies (India and other low-quality markets)
BLOCKED_CURRENCIES = {"INR", "PKR", "BDT", "LKR", "NPR", "PHP", "NGN", "GHS", "KES", "TZS"}

class FreelancerAgent(BaseSourceAgent):
    @property
    def source_name(self) -> str:
        return "freelancer"

    async def collect(self) -> list[RawSignalCreate]:
        signals = []
        queries = ["AI", "agents", "Voice AI", "workflow", "automation"]
        
        try:
            async with httpx.AsyncClient() as client:
                for q in queries:
                    # Fetch 150 results since we are filtering by region
                    url = f"https://www.freelancer.com/api/projects/0.1/projects/active?query={q}&limit=150&compact=false"
                    resp = await client.get(url, timeout=15.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        projects = data.get("result", {}).get("projects", [])
                        
                        for p in projects:
                            # Avoid duplicates across queries
                            ext_id = f"freelancer-{p.get('id')}"
                            if any(s.external_id == ext_id for s in signals):
                                continue
                                
                            currency_code = p.get("currency", {}).get("code", "")
                            
                            # Block explicitly excluded currencies (India etc.)
                            if currency_code in BLOCKED_CURRENCIES:
                                continue
                                
                            # Only allow target regions
                            if currency_code not in ALLOWED_CURRENCIES:
                                continue
                                
                            desc = p.get("preview_description", "")
                            title = p.get("title", "")
                            seo_url = p.get("seo_url", "")

                            # Content-level geo filter: reject India-targeted posts
                            combined_text = (title + " " + desc).lower()
                            india_keywords = [
                                "delhi ncr", "people based in india", "india only", "indian only",
                                "based in india", "india-based", "mumbai based", "bangalore based",
                                "hyderabad based", "pune based", "chennai based", "kolkata based",
                                ",1", " inr", "rupees",
                                "apply only indian", "indian developers", "indian freelancer",
                                "only for india", "india based freelancer", "indian candidates",
                            ]
                            if any(kw in combined_text for kw in india_keywords):
                                continue
                            
                            budget = p.get("budget", {})
                            currency = p.get("currency", {})
                            b_min = budget.get("minimum", 0)
                            b_max = budget.get("maximum", 0)
                            c_sign = currency.get("sign", "$")
                            country_label = ALLOWED_CURRENCIES.get(currency_code, currency_code)
                            
                            meta = {
                                "Budget": f"{c_sign}{b_min} - {c_sign}{b_max}" if b_max else "Hourly/Negotiable",
                                "Type": str(p.get("type", "unknown")).title(),
                                "Bids": p.get("bid_stats", {}).get("bid_count", 0),
                                "Country": country_label,
                                "Currency": currency_code,
                            }
                            
                            signals.append(RawSignalCreate(
                                source="freelancer",
                                external_id=ext_id,
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

