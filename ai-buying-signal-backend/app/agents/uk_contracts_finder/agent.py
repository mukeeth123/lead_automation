import httpx
from datetime import datetime, timezone, timedelta
from app.schemas.signal import RawSignalCreate
import re

class UKContractsFinderAgent:
    def __init__(self):
        self.api_url = "https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search"
        self.days = 14
        
    def flatten_text(self, value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, list):
            return " ".join(self.flatten_text(x) for x in value)
        if isinstance(value, dict):
            return " ".join(self.flatten_text(v) for v in value.values())
        return str(value)

    def find_url(self, release):
        candidates = [
            release.get("url"),
            release.get("uri")
        ]
        tender = release.get("tender", {})
        if "documents" in tender and isinstance(tender["documents"], list):
            for doc in tender["documents"]:
                if isinstance(doc, dict) and doc.get("url"):
                    candidates.append(doc["url"])
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.startswith("http"):
                return candidate
        return "https://www.contractsfinder.service.gov.uk"

    async def collect(self):
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=self.days)
        params = {
            "publishedFrom": start_date.strftime("%Y-%m-%d"),
            "publishedTo": now.strftime("%Y-%m-%d"),
            "limit": 100
        }
        
        signals = []
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.api_url, params=params, timeout=30.0)
                if resp.status_code == 200:
                    data = resp.json()
                    releases = data.get("releases", [])
                    seen = set()
                    
                    for release in releases:
                        text = self.flatten_text(release).lower()
                        # Simple keyword filtering for IT/software contracts
                        keywords = ["software", "development", "data", "cloud", "artificial intelligence", "integration", "crm", "erp", "digital"]
                        if not any(k in text for k in keywords):
                            continue
                            
                        tender = release.get("tender", {})
                        buyer = release.get("buyer", {})
                        
                        release_id = release.get("id") or release.get("ocid") or tender.get("title", "unknown")
                        if release_id in seen:
                            continue
                        seen.add(release_id)
                        
                        title = tender.get("title", "UK Government Contract")
                        desc = tender.get("description", "")
                        
                        published_str = release.get("date")
                        pub_date = now
                        if published_str:
                            try:
                                pub_date = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                            except:
                                pass
                                
                        signals.append(RawSignalCreate(
                            source="uk_contracts_finder",
                            external_id=f"cf-{release_id}",
                            title=title,
                            content=desc[:1500] if desc else text[:1500],
                            author=buyer.get("name", "UK Government"),
                            url=self.find_url(release),
                            published_at=pub_date
                        ))
        except Exception as e:
            print(f"ContractsFinder Error: {e}")
        return signals
