import httpx
from datetime import datetime, timezone
import dateutil.parser
from app.schemas.signal import RawSignalCreate
import re

class RemotiveAgent:
    def __init__(self):
        # Unauthenticated JSON API
        self.api_urls = [
            "https://remotive.com/api/remote-jobs?category=software-dev",
            "https://remotive.com/api/remote-jobs?category=marketing"
        ]

    async def collect(self):
        signals = []
        try:
            async with httpx.AsyncClient() as client:
                for url in self.api_urls:
                    resp = await client.get(url, timeout=10.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        jobs = data.get("jobs", [])
                    
                    for job in jobs[:5]:
                        title = job.get("title", "")
                        clean_desc = re.sub(r'<[^>]+>', '', job.get("description", ""))
                        url = job.get("url", "")
                        company = job.get("company_name", "Remotive Company")
                        
                        pub_date = datetime.now(timezone.utc)
                        pub_date_str = job.get("publication_date")
                        if pub_date_str:
                            try:
                                pub_date = dateutil.parser.parse(pub_date_str)
                            except:
                                pass

                        signals.append(RawSignalCreate(
                            source="remotive",
                            external_id=f"remotive-{job.get('id')}",
                            title=title,
                            content=clean_desc[:1000],
                            author=company,
                            url=url,
                            published_at=pub_date
                        ))
        except Exception as e:
            print(f"Remotive Error: {e}")
            
        return signals
