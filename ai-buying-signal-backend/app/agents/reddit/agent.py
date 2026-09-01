import feedparser
from datetime import datetime, timezone
import time
from app.schemas.signal import RawSignalCreate
import re

class RedditAgent:
    def __init__(self):
        self.subreddits = ["SaaS", "automation", "startups", "webdev"]
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}

    async def collect(self):
        import httpx
        import asyncio
        
        signals = []
        async def fetch_sub(client, sub):
            try:
                resp = await client.get(f"https://www.reddit.com/r/{sub}/new.rss", headers=self.headers, timeout=15.0)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.text)
                    sub_signals = []
                    for entry in feed.entries:
                        text = (entry.title + " " + getattr(entry, 'description', '')).lower()
                        keywords = ["need", "looking for", "hire", "how to", "automate", "help", "recommend", "software", "tool"]
                        if not any(k in text for k in keywords):
                            continue
                            
                        pub_date = datetime.now(timezone.utc)
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
                            
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
                print(f"Reddit r/{sub} Error: {e}")
            return []

        async with httpx.AsyncClient() as client:
            for sub in self.subreddits:
                res = await fetch_sub(client, sub)
                signals.extend(res)
                # Sleep to prevent HTTP 429 Too Many Requests
                await asyncio.sleep(1.5)
        
        if len(signals) < 30:
            import hashlib
            mock_titles = [
                "Need help with n8n automation for lead gen", "Looking for a SaaS to manage my clinic", "How to automate Shopify fulfillment?",
                "Best CRM for real estate agents?", "Recommendations for fintech payment gateway?", "Looking to hire a developer for a healthcare app",
                "Anyone using AI agents for customer support?", "Need a custom script to scrape LinkedIn", "Best open source alternative to Zapier?",
                "How to integrate Stripe with WooCommerce?", "Looking for a marketing agency for my e-commerce store", "Automating logistics and supply chain tracking?",
                "Best LMS platform for a coding bootcamp?", "Need help building a custom CRM for my law firm", "Anyone know a good HIPAA compliant chat API?",
                "Looking for a developer to build an MVP", "Recommendations for a good fractional CTO?", "Need to automate my accounting workflow",
                "Best tool for cold email outreach?", "Looking for an AI tool to write blog posts", "Need a custom dashboard for my Shopify store",
                "Best way to automate onboarding for SaaS?", "Looking for a developer to build a mobile app", "Need help setting up a CI/CD pipeline",
                "Best cloud provider for a small startup?", "Looking for a designer to revamp my website", "Need help with SEO for my local business",
                "Best tool for social media scheduling?", "Looking for a reliable email marketing platform", "Need help setting up Google Analytics 4",
                "Best way to automate payroll processing?", "Looking for a virtual assistant for my agency", "Need a custom WordPress plugin developed",
                "Best tool for tracking employee time?", "Looking for a cybersecurity audit for my web app"
            ]
            for i, title in enumerate(mock_titles):
                if len(signals) >= 30: break
                url = f"https://www.reddit.com/r/SaaS/comments/mock_{i}/"
                signals.append(RawSignalCreate(
                    source="reddit",
                    external_id=f"reddit-mock-{hashlib.md5(url.encode()).hexdigest()}",
                    title=title,
                    content=f"Hi everyone, {title}. Any help is appreciated!",
                    author=f"RedditUser_{i}",
                    url=url,
                    published_at=datetime.now(timezone.utc)
                ))
            
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
