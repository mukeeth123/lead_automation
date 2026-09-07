import httpx
from datetime import datetime, timezone
import time
from app.schemas.signal import RawSignalCreate
import html

class StackExchangeAgent:
    def __init__(self):
        # ServerFault for enterprise/IT needs
        self.api_url = "https://api.stackexchange.com/2.3/questions"
        self.tags = [
            "aws", "web-development", "seo", "machine-learning", 
            "cloud-migration", "artificial-intelligence", "automation", "voice-ai"
        ]

    async def collect(self):
        signals = []
        try:
            async with httpx.AsyncClient() as client:
                for tag in self.tags:
                    params = {
                        "site": "serverfault",
                        "tagged": tag,
                        "sort": "creation",
                        "order": "desc",
                        "pagesize": 5,
                        "filter": "withbody" # gets the body of the question
                    }
                    resp = await client.get(self.api_url, params=params, timeout=10.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        for item in data.get("items", []):
                            title = html.unescape(item.get("title", ""))
                            body = html.unescape(item.get("body_markdown", item.get("body", "")))
                            
                            pub_date = datetime.now(timezone.utc)
                            creation = item.get("creation_date")
                            if creation:
                                pub_date = datetime.fromtimestamp(creation, timezone.utc)
                                
                            signals.append(RawSignalCreate(
                                source="stackexchange",
                                external_id=f"se-{item.get('question_id')}",
                                title=title,
                                content=body[:1000],
                                author=item.get("owner", {}).get("display_name", "SysAdmin"),
                                url=item.get("link", ""),
                                published_at=pub_date
                            ))
        except Exception as e:
            print(f"StackExchange Error: {e}")
            
        return signals
