import hashlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional
from bs4 import BeautifulSoup
from app.schemas.signal import RawSignalCreate

class BubbleForumParser:
    def parse_item(self, item: dict) -> Optional[RawSignalCreate]:
        try:
            title = item.get("title", "")
            url = item.get("link", "")
            
            if not title or not url:
                return None
                
            external_id = f"bub-{hashlib.md5(url.encode()).hexdigest()}"
            
            content = ""
            if 'summary' in item:
                soup = BeautifulSoup(item['summary'], 'html.parser')
                content = soup.get_text(separator=' ', strip=True)
            elif 'content' in item and len(item['content']) > 0:
                soup = BeautifulSoup(item['content'][0].get('value', ''), 'html.parser')
                content = soup.get_text(separator=' ', strip=True)
                
            if not content:
                content = title

            author_name = "Unknown"
            if 'author' in item:
                author_name = item['author']
                
            published_at = datetime.now(timezone.utc)
            if 'published' in item:
                try:
                    published_at = parsedate_to_datetime(item['published'])
                except Exception:
                    pass
                    
            return RawSignalCreate(
                source="bubble_forum",
                external_id=external_id,
                title=title,
                content=content,
                author=author_name,
                url=url,
                published_at=published_at
            )
        except Exception as e:
            return None
