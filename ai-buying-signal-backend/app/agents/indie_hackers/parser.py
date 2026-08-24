import hashlib
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import email.utils
from app.schemas.signal import RawSignalCreate

class IndieHackersParser:
    def parse_item(self, item) -> RawSignalCreate:
        try:
            # Parse published date
            published = item.get('published', '')
            if published:
                parsed_time = email.utils.parsedate_to_datetime(published)
                published_at = parsed_time if parsed_time else datetime.now(timezone.utc)
            else:
                published_at = datetime.now(timezone.utc)
            
            # Clean HTML from summary
            html = item.get("summary", "")
            text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
            
            url = item.get("link", "")
            external_id = f"ih-{hashlib.md5(url.encode()).hexdigest()}"
            
            return RawSignalCreate(
                source="indiehackers",
                external_id=external_id,
                title=item.get("title", ""),
                content=text,
                author=item.get("author", "Unknown"),
                url=url,
                published_at=published_at
            )
        except Exception:
            return None
