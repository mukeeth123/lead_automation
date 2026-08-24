import asyncio
from app.api.v1.leads import get_leads

async def main():
    leads = await get_leads()
    print(f"Total leads: {len(leads)}")
    for l in leads:
        print(l["source"])

if __name__ == "__main__":
    asyncio.run(main())
