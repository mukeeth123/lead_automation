import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.agents.n8n.agent import N8nAgent

async def main():
    print("Initializing n8n agent...")
    agent = N8nAgent()
    
    print(f"Running health check for {agent.source_name}...")
    is_healthy = await agent.health_check()
    print(f"Health check passed: {is_healthy}")
    
    if is_healthy:
        print("\nCollecting signals from the live RSS feed...")
        signals = await agent.collect()
        print(f"\nCollected {len(signals)} signals!")
        
        print("\n--- Sample of first 2 signals ---")
        for i, signal in enumerate(signals[:2]):
            print(f"\nSignal #{i+1}:")
            # Convert the Pydantic model to a dict and print as formatted JSON
            print(json.dumps(signal.model_dump(mode='json'), indent=2))

if __name__ == "__main__":
    asyncio.run(main())
