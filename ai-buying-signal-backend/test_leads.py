import asyncio
import httpx

async def test_leads():
    print("Sending request to /api/v1/leads...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.get("http://127.0.0.1:8000/api/v1/leads")
            print(f"Status Code: {response.status_code}")
            
            data = response.json()
            if "leads" in data:
                leads = data["leads"]
                print(f"Retrieved {len(leads)} leads.")
                
                # Print the first lead as an example
                if leads:
                    print("\nFirst Lead Sample:")
                    print("="*40)
                    lead = leads[0]
                    for k, v in lead.items():
                        print(f"{k}: {v}")
            else:
                print("Response does not contain 'leads':")
                print(data)
                
        except Exception as e:
            print(f"Error connecting to server: {e}")

if __name__ == "__main__":
    asyncio.run(test_leads())
