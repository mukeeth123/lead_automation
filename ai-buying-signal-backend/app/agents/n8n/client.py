import httpx
import feedparser
from .config import N8N_RSS_URL, TIMEOUT_SECONDS

class N8nClient:
    def __init__(self):
        self.url = N8N_RSS_URL

    async def fetch_feed(self) -> str:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(self.url)
            response.raise_for_status()
            return response.text

    def parse_feed(self, content: str):
        return feedparser.parse(content)
