import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

BASE_URL = "https://www.startupnetworks.co.uk"
ACTIVITY_URL = "https://www.startupnetworks.co.uk/discover"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(
    ACTIVITY_URL,
    headers=headers,
    timeout=30
)

print("Status:", response.status_code)
print("Page size:", len(response.text))

soup = BeautifulSoup(response.text, "html.parser")

# Extract possible discussion links
posts = []
seen_urls = set()

for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)
    url = urljoin(BASE_URL, a["href"])

    if not title:
        continue

    if ("/topic/" in url or "/forum/" in url or "/jobs/" in url):
        if url not in seen_urls:
            posts.append({
                "title": title,
                "url": url
            })
            seen_urls.add(url)

print("Discussion links found:", len(posts))
print(posts[:10])
