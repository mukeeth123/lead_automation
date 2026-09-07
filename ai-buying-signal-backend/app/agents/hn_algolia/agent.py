import httpx
from datetime import datetime, timezone
import time
from app.schemas.signal import RawSignalCreate
import re

class HNAlgoliaAgent:
    def __init__(self):
        self.api_url = "https://hn.algolia.com/api/v1/search_by_date"
        self.queries = [
            '"looking for a developer"',
            '"need a developer"',
            '"freelance developer"',
            '"looking for an agency"',
            '"need an agency"',
            '"hiring a freelancer"',
            '"need someone to build"',
            '"looking for a technical co-founder"'
        ]

    async def collect(self):
        signals = []
        try:
            # 14 days ago timestamp
            timestamp_14_days_ago = int(time.time()) - (14 * 24 * 60 * 60)
            
            async with httpx.AsyncClient() as client:
                for q in self.queries:
                    # Using numericFilters for created_at_i to only get recent posts
                    url = f"{self.api_url}?query={q}&numericFilters=created_at_i>{timestamp_14_days_ago}&hitsPerPage=50"
                    resp = await client.get(url, timeout=10.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        for item in data.get("hits", []):
                            # Ensure we have text to analyze
                            content = item.get("comment_text") or item.get("story_text") or ""
                            if not content:
                                continue
                                
                            clean_desc = re.sub(r'<[^>]+>', '', content)
                            
                            # Skip if it's too old anyway just to be safe
                            pub_date = datetime.now(timezone.utc)
                            if "created_at_i" in item:
                                pub_date = datetime.fromtimestamp(item["created_at_i"], timezone.utc)
                                
                            if (datetime.now(timezone.utc) - pub_date).days > 14:
                                continue

                            signals.append(RawSignalCreate(
                                source="hn_algolia",
                                external_id=f"hn-{item.get('objectID')}",
                                title=f"Hacker News Match",
                                content=clean_desc[:1000],
                                author=item.get("author", "HN User"),
                                url=f"https://news.ycombinator.com/item?id={item.get('objectID')}",
                                published_at=pub_date
                            ))
        except Exception as e:
            print(f"HN Algolia Error: {e}")
            
        return signals
