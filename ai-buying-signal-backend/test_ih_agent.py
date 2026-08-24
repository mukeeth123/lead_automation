import asyncio
from app.agents.indie_hackers.agent import IndieHackersAgent

async def main():
    agent = IndieHackersAgent()
    signals = await agent.collect()
    print(f"Collected {len(signals)} signals")
    for s in signals:
        print(s.title.encode('utf-8'))

if __name__ == "__main__":
    asyncio.run(main())
