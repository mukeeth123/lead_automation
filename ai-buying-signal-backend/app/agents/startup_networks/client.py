import httpx
from bs4 import BeautifulSoup

class StartupNetworksClient:
    def __init__(self):
        self.url = "https://www.startupnetworks.co.uk/discover"
        self.headers = {
            "User-Agent": "Mozilla/5.0"
        }

    async def fetch_page(self) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.url, headers=self.headers)
            response.raise_for_status()
            return response.text
