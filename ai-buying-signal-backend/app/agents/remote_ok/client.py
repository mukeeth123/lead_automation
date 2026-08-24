import httpx

class RemoteOKClient:
    def __init__(self):
        self.url = "https://remoteok.com/api"

    async def fetch_jobs(self) -> list:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            response.raise_for_status()
            return response.json()
