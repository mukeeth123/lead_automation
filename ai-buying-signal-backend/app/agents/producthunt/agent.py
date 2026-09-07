import os
import httpx
from datetime import datetime, timezone
import dateutil.parser
from app.schemas.signal import RawSignalCreate
from dotenv import load_dotenv

load_dotenv()

class ProductHuntAgent:
    def __init__(self):
        self.client_id = os.getenv("PRODUCT_HUNT_CLIENT_ID")
        self.client_secret = os.getenv("PRODUCT_HUNT_CLIENT_SECRET")
        self.oauth_url = "https://api.producthunt.com/v2/oauth/token"
        self.graphql_url = "https://api.producthunt.com/v2/api/graphql"

    async def get_token(self, client: httpx.AsyncClient):
        if not self.client_id or not self.client_secret:
            return None
            
        try:
            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials"
            }
            resp = await client.post(self.oauth_url, json=payload, timeout=10.0)
            if resp.status_code == 200:
                return resp.json().get("access_token")
        except Exception as e:
            print(f"ProductHunt Token Error: {e}")
        return None

    async def collect(self):
        signals = []
        if not self.client_id:
            return signals

        try:
            async with httpx.AsyncClient() as client:
                token = await self.get_token(client)
                if not token:
                    return signals
                    
                query = """
                query {
                  posts(first: 10) {
                    edges {
                      node {
                        id
                        name
                        tagline
                        description
                        url
                        createdAt
                        user {
                          name
                        }
                      }
                    }
                  }
                }
                """
                headers = {"Authorization": f"Bearer {token}"}
                resp = await client.post(self.graphql_url, json={"query": query}, headers=headers, timeout=15.0)
                
                if resp.status_code == 200:
                    data = resp.json()
                    edges = data.get("data", {}).get("posts", {}).get("edges", [])
                    
                    for edge in edges:
                        node = edge.get("node", {})
                        if not node:
                            continue
                            
                        title = f"{node.get('name', 'Startup')} - {node.get('tagline', '')}"
                        description = node.get("description", "")
                        
                        # Product Hunt intent filtering: Boost solo makers, no-code, productivity
                        desc_lower = (description + " " + title).lower()
                        if any(k in desc_lower for k in ["no-code", "nocode", "solo maker", "indie hacker", "indie maker", "built by one", "productivity", "saas", "dev tool", "developer tool"]):
                            title = f"[HOT STARTUP] {title}"
                            description = f"Potential scale-up opportunity: {description}"
                            
                        pub_date = datetime.now(timezone.utc)
                        created_at_str = node.get("createdAt")
                        if created_at_str:
                            try:
                                pub_date = dateutil.parser.parse(created_at_str)
                            except:
                                pass
                                
                        author = node.get("user", {}).get("name", "ProductHunt User")

                        signals.append(RawSignalCreate(
                            source="producthunt",
                            external_id=f"ph-{node.get('id')}",
                            title=title[:255],
                            content=description[:1000] if description else title[:1000],
                            author=author,
                            url=node.get("url", "https://producthunt.com"),
                            published_at=pub_date
                        ))
        except Exception as e:
            print(f"ProductHunt Error: {e}")
            
        return signals
