import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone
from typing import List
from app.schemas.signal import RawSignalCreate

class UKBusinessForumsParser:
    def __init__(self):
        self.base_url = "https://www.ukbusinessforums.co.uk"

    def parse_page(self, html: str) -> List[RawSignalCreate]:
        soup = BeautifulSoup(html, "html.parser")
        signals = []
        seen_urls = set()

        for a in soup.find_all("a", href=True):
            title = a.get_text(" ", strip=True)
            raw_url = urljoin(self.base_url, a["href"])

            if not title:
                continue

            if "/threads/" in raw_url:
                parsed = urlparse(raw_url)
                url = parsed.scheme + "://" + parsed.netloc + parsed.path
                if not url.endswith('/'):
                    url += '/'

                if url not in seen_urls:
                    seen_urls.add(url)
                    external_id = f"ukbf-{hashlib.md5(url.encode()).hexdigest()}"
                    
                    signal = RawSignalCreate(
                        source="uk_business_forums",
                        external_id=external_id,
                        title=title,
                        content=title,
                        author="Unknown",
                        url=url,
                        published_at=datetime.now(timezone.utc)
                    )
                    signals.append(signal)

        return signals
