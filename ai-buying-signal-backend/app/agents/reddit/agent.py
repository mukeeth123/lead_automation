import feedparser
from datetime import datetime, timezone
import time
from app.schemas.signal import RawSignalCreate
import re

class RedditAgent:
    def __init__(self):
        self.subreddits = ["SaaS", "automation", "startups", "webdev"]
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    async def collect(self):
        signals = []
        for sub in self.subreddits:
            try:
                # We use feedparser.parse directly on the URL which handles the XML parsing
                # But sometimes we need to pass a User-Agent via httpx first to avoid 429
                import httpx
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"https://www.reddit.com/r/{sub}/new.rss", headers=self.headers, timeout=15.0)
                    if resp.status_code == 200:
                        feed = feedparser.parse(resp.text)
                        for entry in feed.entries:
                            # Basic keyword filtering to avoid pure spam
                            text = (entry.title + " " + getattr(entry, 'description', '')).lower()
                            keywords = ["need", "looking for", "hire", "how to", "automate", "help", "recommend", "software", "tool"]
                            if not any(k in text for k in keywords):
                                continue
                                
                            pub_date = datetime.now(timezone.utc)
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
                                
                            desc = getattr(entry, 'description', '')
                            # Strip basic HTML tags
                            clean_desc = re.sub(r'<[^>]+>', '', desc)
                            
                            signals.append(RawSignalCreate(
                                source="reddit",
                                external_id=f"reddit-{entry.id}",
                                title=entry.title,
                                content=clean_desc[:1000],
                                author=getattr(entry, 'author', 'Reddit User'),
                                url=entry.link,
                                published_at=pub_date
                            ))
            except Exception as e:
                print(f"Reddit r/{sub} Error: {e}")
        return signals
