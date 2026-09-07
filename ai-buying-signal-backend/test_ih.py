import asyncio
import httpx
import feedparser

async def main():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get("https://feed.indiehackers.world/posts.rss?q=developer", timeout=10.0)
            feed = feedparser.parse(resp.text)
            for entry in feed.entries[:3]:
                print(f"Title: {entry.title}")
                print(f"Link: {entry.link}")
                print("-" * 20)
        except Exception as e:
            print(f"IH Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
