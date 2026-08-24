import asyncio
from app.agents.indie_hackers.client import IndieHackersClient

async def main():
    client = IndieHackersClient()
    links = await client.fetch_post_links()
    print(f"Found {len(links)} links")
    for link in links:
        print(link)

if __name__ == "__main__":
    asyncio.run(main())
