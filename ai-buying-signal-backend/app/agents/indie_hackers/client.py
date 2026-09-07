import httpx
import feedparser

class IndieHackersClient:
    def __init__(self):
        self.base_url = "https://feed.indiehackers.world/posts.rss"

    async def fetch_feed(self, url: str = None) -> str:
        target_url = url if url else self.base_url
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(target_url)
            response.raise_for_status()
            return response.text

    def parse_feed(self, content: str):
        return feedparser.parse(content)
