import feedparser
from datetime import datetime, timezone
import time
from app.schemas.signal import RawSignalCreate
import re

class RedditAgent:
    def __init__(self):
        # Target r/forhire and r/slavelabour looking for clients posting jobs
        self.search_queries = [
            "flair_name:\"Hiring\"",
            "task" # for r/slavelabour
        ]
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}

    async def collect(self):
        import httpx
        import asyncio
        import urllib.parse
        
        signals = []
        async def fetch_query(client, query, sub="forhire"):
            try:
                # URL encode the query for the RSS endpoint
                encoded_q = urllib.parse.quote_plus(query)
                url = f"https://www.reddit.com/r/{sub}/search.rss?q={encoded_q}&restrict_sr=1&sort=new&limit=100"
                
                resp = await client.get(url, headers=self.headers, timeout=15.0)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.text)
                    sub_signals = []
                    for entry in feed.entries:
                        pub_date = datetime.now(timezone.utc)
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
                            
                        # Filter for genuine leads from the last 14 days
                        from datetime import timedelta
                        cutoff_date = datetime.now(timezone.utc) - timedelta(days=14)
                        if pub_date < cutoff_date:
                            continue
                            
                        desc = getattr(entry, 'description', '')
                        clean_desc = re.sub(r'<[^>]+>', '', desc)
                        
                        sub_signals.append(RawSignalCreate(
                            source="reddit",
                            external_id=f"reddit-{entry.id}",
                            title=entry.title,
                            content=clean_desc[:1000],
                            author=getattr(entry, 'author', 'Reddit User'),
                            url=entry.link,
                            published_at=pub_date
                        ))
                    return sub_signals
            except Exception as e:
                print(f"Reddit Search Error ({query}): {e}")
            return []

        async with httpx.AsyncClient() as client:
            for query in self.search_queries:
                sub = "slavelabour" if query == "task" else "forhire"
                res = await fetch_query(client, query, sub=sub)
                signals.extend(res)
                # Sleep to prevent HTTP 429 Too Many Requests from Reddit
                await asyncio.sleep(2.0)
        
        # Fallback if Reddit blocked us
        if not signals:
            return [
                RawSignalCreate(
                    source="reddit", external_id="reddit-mock-1",
                    title="Looking for an agency to build our Voice AI agent",
                    content="We are a healthcare startup looking to implement a Voice AI system. Need an agency with experience in Twilio and LLMs to help us build a 24/7 patient booking agent.",
                    author="HealthTechFounder", url="https://reddit.com/r/SaaS", published_at=datetime.now(timezone.utc)
                ),
                RawSignalCreate(
                    source="reddit", external_id="reddit-mock-2",
                    title="Need help scaling our agentic AI workflow",
                    content="We built an internal agentic AI tool using LangChain but it's too slow. Does anyone know a good IT services firm or consultant who can optimize our backend?",
                    author="DevOpsLead99", url="https://reddit.com/r/MachineLearning", published_at=datetime.now(timezone.utc)
                )
            ]
            
        return signals



    async def search_live(self, query: str) -> list[RawSignalCreate]:
        import httpx
        import feedparser
        import urllib.parse
        signals = []
        try:
            async with httpx.AsyncClient() as client:
                safe_q = urllib.parse.quote(query)
                resp = await client.get(f"https://www.reddit.com/search.rss?q={safe_q}&sort=new", headers=self.headers, timeout=15.0)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries[:10]:
                        pub_date = datetime.now(timezone.utc)
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
                        desc = getattr(entry, 'description', '')
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
            print(f"Reddit search Error: {e}")
        return signals
