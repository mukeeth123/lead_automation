import os
import logging
import httpx
from datetime import datetime, timezone, timedelta
from typing import List
from app.agents.base.agent import BaseSourceAgent
from app.schemas.signal import RawSignalCreate

logger = logging.getLogger(__name__)

class GithubAgent(BaseSourceAgent):
    @property
    def source_name(self) -> str:
        return "github"

    async def collect(self) -> List[RawSignalCreate]:
        signals = []
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            logger.warning("GITHUB_TOKEN not found in .env, skipping GitHub agent")
            return []
            
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}",
            "User-Agent": "AI-Buying-Signal-Bot"
        }
        
        # Look for issues created in the last 7 days asking for help/freelancers/agencies
        since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')
        
        queries = [
            f'is:issue is:open ("looking for an agency" OR "development partner" OR "consultant" OR "freelancer") -label:"good first issue" -label:"documentation" created:>{since}',
            f'is:issue is:open ("paid project" OR "budget" OR "outsourcing" OR "need a developer" OR "hiring") -label:"good first issue" -label:"documentation" created:>{since}',
            f'is:issue is:open ("implementation" OR "integration" OR "migration" OR "custom software") -label:"good first issue" -label:"documentation" created:>{since}',
            f'is:issue is:open ("automation" OR "AI implementation" OR "LLM implementation" OR "RAG implementation") -label:"good first issue" -label:"documentation" created:>{since}'
        ]
        
        try:
            import asyncio
            async def fetch_query(q):
                async with httpx.AsyncClient() as client:
                    resp = await client.get("https://api.github.com/search/issues", params={"q": q, "sort": "created", "order": "desc", "per_page": 20}, headers=headers, timeout=15.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        sub_signals = []
                        for item in data.get("items", []):
                            pub_date = datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                            body = item.get("body") or ""
                            
                            sub_signals.append(RawSignalCreate(
                                source="github",
                                external_id=f"github-{item['id']}",
                                title=item.get("title", ""),
                                content=body[:1000],
                                author=item.get("user", {}).get("login", "Unknown"),
                                url=item.get("html_url", ""),
                                published_at=pub_date
                            ))
                        return sub_signals
                    else:
                        logger.error(f"GitHub API error: {resp.status_code} {resp.text}")
                        return []
                        
            tasks = [fetch_query(q) for q in queries]
            results = await asyncio.gather(*tasks)
            for r in results:
                signals.extend(r)
                
            # Deduplicate by external_id
            unique_signals = {s.external_id: s for s in signals}
            signals = list(unique_signals.values())
            
            logger.info(f"Successfully collected {len(signals)} signals from {self.source_name}")
            
        except Exception as e:
            logger.error(f"Error collecting from {self.source_name}: {e}")
            
        return signals

    async def health_check(self) -> bool:
        return len(await self.collect()) > 0

    async def search_live(self, query: str) -> List[RawSignalCreate]:
        signals = []
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            return []
            
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}",
            "User-Agent": "AI-Buying-Signal-Bot"
        }
        
        since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')
        q = f'{query} is:issue is:open -label:"good first issue" -label:"documentation" created:>{since}'
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://api.github.com/search/issues", params={"q": q, "sort": "created", "order": "desc", "per_page": 10}, headers=headers, timeout=15.0)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("items", []):
                        pub_date = datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        body = item.get("body") or ""
                        signals.append(RawSignalCreate(
                            source="github",
                            external_id=f"github-{item['id']}",
                            title=item.get("title", ""),
                            content=body[:1000],
                            author=item.get("user", {}).get("login", "Unknown"),
                            url=item.get("html_url", ""),
                            published_at=pub_date
                        ))
        except Exception as e:
            logger.error(f"Error live searching github: {e}")
        return signals
