import httpx
import feedparser

class IndieHackersClient:
    def __init__(self):
        self.url = "https://feed.indiehackers.world/posts.rss"

    async def fetch_feed(self) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.url)
            response.raise_for_status()
            return response.text

    def parse_feed(self, content: str):
        return feedparser.parse(content)
