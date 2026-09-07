import asyncio
import httpx
import feedparser

async def fetch_indie_hackers(client):
    print("Scraping Indie Hackers...")
    url = "https://feed.indiehackers.world/posts.rss?q=developer"
    resp = await client.get(url, timeout=10.0)
    feed = feedparser.parse(resp.text)
    
    leads = []
    for entry in feed.entries[:5]:
        leads.append({
            "source": "Indie Hackers",
            "title": entry.title,
            "genuine_url": entry.link
        })
    return leads

async def fetch_reddit(client):
    print("Scraping Reddit (r/Entrepreneur)...")
    url = "https://www.reddit.com/r/Entrepreneur/search.rss?q=developer&restrict_sr=1&sort=new&limit=5"
    resp = await client.get(url, timeout=10.0)
    feed = feedparser.parse(resp.text)
    
    leads = []
    for entry in feed.entries[:5]:
        leads.append({
            "source": "Reddit",
            "title": entry.title,
            "genuine_url": entry.link
        })
    return leads

async def fetch_remote_ok(client):
    print("Scraping Remote OK...")
    url = "https://remoteok.com/api"
    # Remote OK requires a User-Agent to prevent getting blocked
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    resp = await client.get(url, headers=headers, timeout=10.0)
    data = resp.json()
    
    leads = []
    # Skip index 0 as it is always a legal disclaimer on Remote OK API
    for item in data[1:6]:
        leads.append({
            "source": "Remote OK",
            "title": item.get("position"),
            "company": item.get("company"),
            "genuine_url": item.get("url")
        })
    return leads

async def main():
    # Run all scrapers perfectly in parallel
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            fetch_indie_hackers(client),
            fetch_reddit(client),
            fetch_remote_ok(client)
        )
        
        print("\n" + "="*50)
        print("GENUINE LEADS & URLS EXTRACTED SUCCESSFULLY")
        print("="*50 + "\n")
        
        for source_leads in results:
            for lead in source_leads:
                print(f"[{lead['source']}]")
                if "company" in lead:
                    print(f"Title:   {lead['title']} @ {lead['company']}")
                else:
                    print(f"Title:   {lead['title']}")
                print(f"URL:     {lead['genuine_url']}")
                print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
