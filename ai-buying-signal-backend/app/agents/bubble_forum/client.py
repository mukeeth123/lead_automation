import httpx
import feedparser

class BubbleForumClient:
    def __init__(self):
        self.url = "https://forum.bubble.io/latest.rss"

    async def fetch_feed(self) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            return response.text

    def parse_feed(self, content: str):
        return feedparser.parse(content)
