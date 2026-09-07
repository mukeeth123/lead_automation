import httpx
from datetime import datetime, timezone
import dateutil.parser
from app.schemas.signal import RawSignalCreate
import re

class DiscourseAgent:
    def __init__(self):
        self.forums = [
            "https://community.n8n.io",
            "https://forum.ghost.org",
            "https://discuss.kubernetes.io"
        ]
        # Search queries to filter out general noise and find high-intent posts
        self.queries = [
            "agency order:latest", "marketing order:latest", 
            "web developer order:latest", "ai automation order:latest", 
            "it support order:latest", "staffing order:latest",
            "agentic ai order:latest", "voice ai order:latest", "ai services order:latest"
        ]

    async def collect(self):
        signals = []
        try:
            async with httpx.AsyncClient() as client:
                for forum_url in self.forums:
                    for query in self.queries:
                        # URL encode the query
                        encoded_query = httpx.QueryParams({"q": query})
                        resp = await client.get(f"{forum_url}/search.json", params=encoded_query, timeout=10.0)
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            topics = data.get("topics", [])
                            posts = data.get("posts", [])
                            
                            # Create a map of topic_id to blurb (snippet) from the posts array
                            blurbs = {p.get("topic_id"): p.get("blurb", "") for p in posts if "topic_id" in p}
                            
                            for topic in topics[:2]:
                                title = topic.get("title", "")
                                slug = topic.get("slug", "")
                                topic_id = topic.get("id", "")
                                url = f"{forum_url}/t/{slug}/{topic_id}"
                                content_blurb = blurbs.get(topic_id, title)
                                
                                # Parse date
                                pub_date = datetime.now(timezone.utc)
                                created_at_str = topic.get("created_at")
                                if created_at_str:
                                    try:
                                        pub_date = dateutil.parser.parse(created_at_str)
                                    except:
                                        pass

                                signals.append(RawSignalCreate(
                                    source="discourse",
                                    external_id=f"discourse-{forum_url}-{topic_id}",
                                    title=title,
                                    content=content_blurb,
                                    author="Discourse User",
                                    url=url,
                                    published_at=pub_date
                                ))
        except Exception as e:
            print(f"Discourse Error: {e}")
            
        return signals
