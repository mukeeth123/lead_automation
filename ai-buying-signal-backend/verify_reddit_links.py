import urllib.request
import json

def verify_reddit():
    data = json.loads(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/leads').read())
    reddit_leads = [l for l in data['leads'] if l.get('source') == 'reddit']
    print(f"Total Live Reddit Leads: {len(reddit_leads)}\n")
    for r in reddit_leads:
        print(f"Company: {r.get('company')} ({r.get('country')})")
        print(f"Tech: {r.get('technology')} | Score: {r.get('intentScore')}")
        print(f"Working Link: {r.get('originalUrl')}\n")

if __name__ == '__main__':
    verify_reddit()
