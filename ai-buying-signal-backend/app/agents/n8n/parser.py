from datetime import datetime, timezone
import logging
from app.schemas.signal import RawSignalCreate

logger = logging.getLogger(__name__)

class N8nParser:
    def parse_item(self, item: dict) -> RawSignalCreate | None:
        try:
            external_id = item.get("id") or item.get("link")
            if not external_id:
                logger.warning("n8n item missing external_id, skipping.")
                return None

            title = item.get("title", "")
            content = item.get("description") or item.get("summary", "")
            author = item.get("author", "Unknown")
            url = item.get("link", "")
            
            published_parsed = item.get("published_parsed")
            if published_parsed:
                published_at = datetime(*published_parsed[:6], tzinfo=timezone.utc)
            else:
                published_at = datetime.now(timezone.utc)

            return RawSignalCreate(
                source="n8n",
                external_id=external_id,
                title=title,
                content=content,
                author=author,
                author_url=None,
                url=url,
                published_at=published_at,
                metadata_={"tags": [t.get("term") for t in item.get("tags", [])]} if item.get("tags") else {}
            )
        except Exception as e:
            logger.error(f"Error parsing n8n item: {e}")
            return None
