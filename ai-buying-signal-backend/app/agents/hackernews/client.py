import httpx
import asyncio
from typing import List, Dict, Any

class HackerNewsClient:
    def __init__(self):
        self.base_url = "https://hacker-news.firebaseio.com/v0"

    async def fetch_ask_stories(self, limit: int = 50) -> List[int]:
        """Fetch the latest Ask HN story IDs."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{self.base_url}/askstories.json")
            resp.raise_for_status()
            story_ids = resp.json()
            return story_ids[:limit]

    async def fetch_item(self, client: httpx.AsyncClient, item_id: int) -> Dict[str, Any]:
        """Fetch a single HN item by ID."""
        resp = await client.get(f"{self.base_url}/item/{item_id}.json")
        resp.raise_for_status()
        return resp.json()

    async def fetch_items(self, item_ids: List[int]) -> List[Dict[str, Any]]:
        """Fetch multiple HN items concurrently."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = [self.fetch_item(client, item_id) for item_id in item_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and None results
            valid_items = [
                res for res in results 
                if isinstance(res, dict) and res is not None
            ]
            return valid_items
