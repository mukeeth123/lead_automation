import hashlib
from datetime import datetime, timezone
from typing import Optional
from app.schemas.signal import RawSignalCreate

class RemoteOKParser:
    def parse_item(self, item: dict) -> Optional[RawSignalCreate]:
        try:
            if 'legal' in item:  # Skip the legal info block
                return None
                
            title = item.get("position", "") or item.get("title", "")
            url = item.get("url", "")
            
            if not title or not url:
                return None
                
            external_id = f"remoteok-{hashlib.md5(url.encode()).hexdigest()}"
            content = item.get("description", title)
            company = item.get("company", "Unknown")
            
            # The API provides dates in standard ISO-ish format
            published_at = datetime.now(timezone.utc)
            if 'date' in item:
                try:
                    published_at = datetime.fromisoformat(item['date'].replace("Z", "+00:00"))
                except Exception:
                    pass
                    
            return RawSignalCreate(
                source="remote_ok",
                external_id=external_id,
                title=title,
                content=content,
                author=company,
                url=url,
                published_at=published_at
            )
        except Exception:
            return None
