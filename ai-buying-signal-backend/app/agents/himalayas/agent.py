import httpx
from datetime import datetime, timezone
import time
from app.schemas.signal import RawSignalCreate
import feedparser
import re

class HimalayasAgent:
    def __init__(self):
        self.feed_url = "https://himalayas.app/jobs/rss"

    async def collect(self):
        signals = []
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.feed_url, timeout=10.0)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries[:5]:
                        title = getattr(entry, 'title', '')
                        clean_desc = re.sub(r'<[^>]+>', '', getattr(entry, 'description', ''))
                        
                        pub_date = datetime.now(timezone.utc)
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)

                        signals.append(RawSignalCreate(
                            source="himalayas",
                            external_id=f"himalayas-{getattr(entry, 'id', getattr(entry, 'link', ''))}",
                            title=title,
                            content=clean_desc[:1000],
                            author="Himalayas Startup",
                            url=getattr(entry, 'link', ''),
                            published_at=pub_date
                        ))
        except Exception as e:
            print(f"Himalayas Error: {e}")
            
        return signals
