import httpx
from datetime import datetime, timezone
import time
from app.schemas.signal import RawSignalCreate
import feedparser
import re

class WeWorkRemotelyAgent:
    def __init__(self):
        self.feed_urls = [
            "https://weworkremotely.com/categories/remote-programming-jobs.rss",
            "https://weworkremotely.com/categories/remote-sales-and-marketing-jobs.rss",
            "https://weworkremotely.com/categories/remote-design-jobs.rss",
            "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss"
        ]

    async def collect(self):
        signals = []
        try:
            async with httpx.AsyncClient() as client:
                for url in self.feed_urls:
                    resp = await client.get(url, timeout=10.0)
                    if resp.status_code == 200:
                        feed = feedparser.parse(resp.text)
                        for entry in feed.entries[:5]:
                            title = getattr(entry, 'title', '')
                            clean_desc = re.sub(r'<[^>]+>', '', getattr(entry, 'description', ''))
                            
                            pub_date = datetime.now(timezone.utc)
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)

                            signals.append(RawSignalCreate(
                                source="weworkremotely",
                                external_id=f"wwr-{getattr(entry, 'id', '')}",
                                title=title,
                                content=clean_desc[:1000],
                                author="WWR Client",
                                url=getattr(entry, 'link', ''),
                                published_at=pub_date
                            ))
        except Exception as e:
            print(f"We Work Remotely Error: {e}")
            
        return signals
