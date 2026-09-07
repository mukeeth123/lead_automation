import httpx
from datetime import datetime, timezone
import hashlib
from app.agents.base.agent import BaseSourceAgent
from app.schemas.signal import RawSignalCreate
import logging

logger = logging.getLogger(__name__)

class PeoplePerHourAgent(BaseSourceAgent):
    @property
    def source_name(self) -> str:
        return "peopleperhour"

    async def collect(self) -> list[RawSignalCreate]:
        signals = []
        try:
            async with httpx.AsyncClient() as client:
                url = "https://www.peopleperhour.com/freelance-jobs/technology-programming"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
                }
                resp = await client.get(url, headers=headers, timeout=15.0, follow_redirects=True)
                
                if resp.status_code == 200:
                    from bs4 import BeautifulSoup
                    import json
                    
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    scripts = [s.text for s in soup.find_all('script') if s.text and 'window.PPHReact.initialState=' in s.text]
                    
                    if scripts:
                        script = scripts[0]
                        json_str = script.split('window.PPHReact.initialState=')[1].split('\n')[0].strip('; ')
                        state = json.loads(json_str)
                        
                        projects = state.get("entities", {}).get("projects", {})
                        
                        for proj_id, proj_data in projects.items():
                            attr = proj_data.get("attributes", {})
                            url = attr.get("url", "")
                            title = attr.get("title", "")
                            content = attr.get("proj_desc", "")
                            client_data = attr.get("client", {})
                            author = client_data.get("public_name") or "PPH Client"
                            
                            meta = {}
                            budget = attr.get("budget")
                            currency = attr.get("currency")
                            if budget and currency:
                                meta["Mentioned Pricing"] = f"{currency} {budget}"
                                
                            try:
                                posted_dt = datetime.strptime(attr.get("posted_dt", ""), "%Y-%m-%d %H:%M:%S")
                                published_at = posted_dt.replace(tzinfo=timezone.utc)
                            except:
                                published_at = datetime.now(timezone.utc)
                                
                            signals.append(RawSignalCreate(
                                source="peopleperhour",
                                external_id=f"pph-{proj_id}",
                                title=title,
                                content=content[:1000],
                                author=author,
                                url=url,
                                published_at=published_at,
                                metadata_=meta
                            ))
        except Exception as e:
            logger.error(f"PeoplePerHour search error: {e}")
            
        return signals

    async def health_check(self) -> bool:
        return True
