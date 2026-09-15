import urllib.request
import json
import re

def inspect_thread_comments(thread_id):
    url = f"https://hn.algolia.com/api/v1/search?tags=comment,story_{thread_id}&hitsPerPage=10"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    data = json.loads(urllib.request.urlopen(req).read())
    print(f"Comments for thread {thread_id} ({len(data.get('hits', []))} sampled):")
    for hit in data.get('hits', []):
        text = hit.get('comment_text', '')
        clean = re.sub(r'<[^>]+>', ' ', text)
        print(f"--- Author: {hit.get('author')} ---")
        print(clean[:300] + "...\n")

if __name__ == '__main__':
    inspect_thread_comments("49522897")
