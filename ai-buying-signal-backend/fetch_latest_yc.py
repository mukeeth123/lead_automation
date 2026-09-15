import urllib.request
import urllib.parse
import json

def fetch_latest_yc():
    # 1. Latest "Who is hiring?"
    u1 = 'https://hn.algolia.com/api/v1/search_by_date?query=Ask+HN+Who+is+hiring&tags=story&hitsPerPage=3'
    d1 = json.loads(urllib.request.urlopen(urllib.request.Request(u1, headers={'User-Agent': 'Mozilla/5.0'})).read())
    print("Latest Hiring Threads:")
    for h in d1.get('hits', []):
        print(f"  {h.get('title')} (ID: {h.get('objectID')}, Created: {h.get('created_at')}, Comments: {h.get('num_comments')})")
        
    # 2. Latest "Seeking freelancer"
    u2 = 'https://hn.algolia.com/api/v1/search_by_date?query=Seeking+freelancer&tags=story&hitsPerPage=3'
    d2 = json.loads(urllib.request.urlopen(urllib.request.Request(u2, headers={'User-Agent': 'Mozilla/5.0'})).read())
    print("\nLatest Seeking Freelancer Threads:")
    for h in d2.get('hits', []):
        print(f"  {h.get('title')} (ID: {h.get('objectID')}, Created: {h.get('created_at')}, Comments: {h.get('num_comments')})")

    # 3. Y Combinator Work at a Startup / YC News hiring posts
    u3 = 'https://hn.algolia.com/api/v1/search_by_date?query=YC+hiring&tags=story&hitsPerPage=5'
    d3 = json.loads(urllib.request.urlopen(urllib.request.Request(u3, headers={'User-Agent': 'Mozilla/5.0'})).read())
    print("\nLatest YC Hiring Posts:")
    for h in d3.get('hits', []):
        print(f"  {h.get('title')} (ID: {h.get('objectID')}, URL: {h.get('url')})")

if __name__ == '__main__':
    fetch_latest_yc()
