import feedparser
from datetime import datetime, timezone
import time
from app.schemas.signal import RawSignalCreate
import re

import feedparser
from datetime import datetime, timezone, timedelta
import time
import re
import html
import asyncio
from app.schemas.signal import RawSignalCreate

class RedditAgent:
    def __init__(self):
        self.subreddits = [
            "forhire",
            "freelance_forhire",
            "jobbit",
            "techjobs",
            "remote_jobs"
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        }

    def _is_seller(self, text: str) -> bool:
        t = text.lower()
        seller_patterns = [
            "[for hire]", "[forhire]", "for hire", "[hire me]", "hire me",
            "seeking work", "looking for work", "available for hire", "available for work",
            "i am a developer", "i am an engineer", "i can build", "my portfolio", "my resume",
            "open to work", "hire a developer", "portfolio:"
        ]
        return any(p in t for p in seller_patterns)

    def _is_tech_buyer(self, title: str, desc: str) -> bool:
        combined = (title + " " + desc).lower()
        
        # Check negative non-tech noise
        non_tech = [
            "guitar", "clothing", "storytime", "video editor", "video editing", 
            "drawing", "hoodie", "lending operations", "virtual assistant", 
            "transcription", "handwritten notes", "manga translator", "art commission"
        ]
        if any(w in combined for w in non_tech):
            return False

        # Must have buyer indicators
        buyer_patterns = [
            "[hiring]", "hiring", "[paid]", "looking for a developer", "looking for an engineer",
            "need a developer", "need an engineer", "looking for an agency", "looking to hire",
            "contract implementer", "seeking developer", "developer wanted"
        ]
        if not any(p in title.lower() for p in buyer_patterns):
            return False

        # Must match tech domain keywords
        tech_patterns = [
            "developer", "engineer", "software", "ai", "llm", "rag", "next.js", 
            "react", "python", "full stack", "frontend", "backend", "web", "app", 
            "cloud", "devops", "automation", "api", "database", "supabase", "postgres", 
            "flutter", "ios", "android", "node", "typescript", "implementer"
        ]
        return any(k in combined for k in tech_patterns)

    async def collect(self):
        import httpx
        signals = []

        async with httpx.AsyncClient(headers=self.headers, timeout=15.0) as client:
            for sub in self.subreddits:
                try:
                    url = f"https://www.reddit.com/r/{sub}/new.rss?limit=50"
                    resp = await client.get(url, follow_redirects=True)
                    if resp.status_code == 200:
                        feed = feedparser.parse(resp.text)
                        for entry in feed.entries:
                            title = entry.title
                            desc = getattr(entry, 'description', '')
                            clean_desc = re.sub(r'<[^>]+>', ' ', desc)
                            clean_desc = html.unescape(" ".join(clean_desc.split()))
                            
                            if self._is_seller(title + " " + clean_desc):
                                continue
                            if not self._is_tech_buyer(title, clean_desc):
                                continue

                            link = getattr(entry, 'link', '')
                            if not link or "reddit.com/r/" not in link or "/comments/" not in link:
                                continue

                            pub_date = datetime.now(timezone.utc)
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)

                            signals.append(RawSignalCreate(
                                source="reddit",
                                external_id=f"reddit-{entry.id if hasattr(entry, 'id') else link}",
                                title=title,
                                content=clean_desc[:1500],
                                author=getattr(entry, 'author', 'Reddit Client').replace('/u/', ''),
                                url=link,
                                published_at=pub_date
                            ))
                except Exception as e:
                    print(f"Reddit collect error for r/{sub}: {e}")
                
                await asyncio.sleep(1.5)

        return signals

    async def search_live(self, query: str) -> list[RawSignalCreate]:
        import httpx
        import urllib.parse
        signals = []
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=15.0) as client:
                safe_q = urllib.parse.quote(query)
                resp = await client.get(f"https://www.reddit.com/search.rss?q={safe_q}&sort=new", follow_redirects=True)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries[:15]:
                        title = entry.title
                        desc = getattr(entry, 'description', '')
                        clean_desc = re.sub(r'<[^>]+>', ' ', desc)
                        clean_desc = html.unescape(" ".join(clean_desc.split()))

                        if self._is_seller(title + " " + clean_desc):
                            continue

                        link = getattr(entry, 'link', '')
                        if not link or "reddit.com/r/" not in link or "/comments/" not in link:
                            continue

                        pub_date = datetime.now(timezone.utc)
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)

                        signals.append(RawSignalCreate(
                            source="reddit",
                            external_id=f"reddit-{entry.id if hasattr(entry, 'id') else link}",
                            title=title,
                            content=clean_desc[:1500],
                            author=getattr(entry, 'author', 'Reddit Client').replace('/u/', ''),
                            url=link,
                            published_at=pub_date
                        ))
        except Exception as e:
            print(f"Reddit live search error: {e}")
        return signals
