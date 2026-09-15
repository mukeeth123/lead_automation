import urllib.request
import json

def verify_hr():
    data = json.loads(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/leads').read())
    hr_leads = [l for l in data['leads'] if l.get('source') == 'hackerrank']
    print(f"Total HackerRank Leads: {len(hr_leads)}\n")
    for h in hr_leads[:6]:
        print(f"Company: {h.get('company')} ({h.get('country')})")
        print(f"Tech: {h.get('technology')} | Intent Score: {h.get('intentScore')}")
        print(f"Verified Link: {h.get('originalUrl')}\n")

if __name__ == '__main__':
    verify_hr()
