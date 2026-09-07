import httpx
from datetime import datetime, timezone
import time
from app.schemas.signal import RawSignalCreate
import feedparser
import re

class MastodonAgent:
    def __init__(self):
        # Searching popular instances via RSS tags
        self.instances = ["https://mastodon.social", "https://fosstodon.org"]
        self.tags = [
            "webdev", "marketing", "hiring", "automation", 
            "ai", "itservices", "staffing", "agentic", "voiceai"
        ]

    async def collect(self):
        signals = []
        try:
            async with httpx.AsyncClient() as client:
                for instance in self.instances:
                    for tag in self.tags:
                        url = f"{instance}/tags/{tag}.rss"
                        resp = await client.get(url, timeout=10.0)
                        if resp.status_code == 200:
                            feed = feedparser.parse(resp.text)
                            for entry in feed.entries:
                                title = getattr(entry, 'title', '')
                                text = (title + " " + getattr(entry, 'description', '')).lower()
                                pub_date = datetime.now(timezone.utc)
                                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                    pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
                                    
                                clean_desc = re.sub(r'<[^>]+>', '', getattr(entry, 'description', ''))
                                
                                signals.append(RawSignalCreate(
                                    source="mastodon",
                                    external_id=f"mastodon-{getattr(entry, 'id', '')}",
                                    title=title if title else f"#{tag} Mention",
                                    content=clean_desc[:1000],
                                    author=getattr(entry, 'author', 'Mastodon User'),
                                    url=entry.link,
                                    published_at=pub_date
                                ))
        except Exception as e:
            print(f"Mastodon Scrape Error: {e}")

        return signals
