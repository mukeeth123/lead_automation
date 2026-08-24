from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.schemas.signal import RawSignalCreate

class HackerNewsParser:
    def parse_item(self, item: Dict[str, Any]) -> Optional[RawSignalCreate]:
        try:
            # We only care about stories that have text
            if item.get("type") != "story":
                return None
                
            text = item.get("text", "")
            title = item.get("title", "")
            
            # If there's no text body, it's just a link, not a good buying signal
            if not text:
                return None
                
            external_id = str(item.get("id"))
            author = item.get("by", "Unknown HN User")
            url = f"https://news.ycombinator.com/item?id={external_id}"
            
            # HN returns UNIX timestamp in seconds
            timestamp = item.get("time")
            if timestamp:
                published_at = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            else:
                published_at = datetime.now(timezone.utc)
                
            # Combine title and text for context
            full_content = f"{title}\n\n{text}"

            return RawSignalCreate(
                source="hackernews",
                external_id=external_id,
                title=title,
                content=full_content,
                url=url,
                author=author,
                published_at=published_at
            )
        except Exception as e:
            print(f"Failed to parse HN item {item.get('id')}: {e}")
            return None
