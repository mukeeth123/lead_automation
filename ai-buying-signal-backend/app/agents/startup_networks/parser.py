import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone
from typing import List
from app.schemas.signal import RawSignalCreate

class StartupNetworksParser:
    def __init__(self):
        self.base_url = "https://www.startupnetworks.co.uk"

    def parse_page(self, html: str) -> List[RawSignalCreate]:
        from urllib.parse import urlparse
        soup = BeautifulSoup(html, "html.parser")
        signals = []
        seen_urls = set()

        for a in soup.find_all("a", href=True):
            title = a.get_text(" ", strip=True)
            raw_url = urljoin(self.base_url, a["href"])

            if not title:
                continue

            # Only process /topic/ or /jobs/ links (ignore /forum/ categories)
            if "/topic/" in raw_url or "/jobs/" in raw_url:
                # Clean URL by removing query parameters (e.g. ?do=findComment)
                parsed = urlparse(raw_url)
                url = parsed.scheme + "://" + parsed.netloc + parsed.path
                if not url.endswith('/'):
                    url += '/'

                if url not in seen_urls:
                    seen_urls.add(url)
                    external_id = f"sn-{hashlib.md5(url.encode()).hexdigest()}"
                    
                    signal = RawSignalCreate(
                        source="startup_networks",
                        external_id=external_id,
                        title=title,
                        content=title,
                        author="Unknown",
                        url=url,
                        published_at=datetime.now(timezone.utc)
                    )
                    signals.append(signal)

        return signals
