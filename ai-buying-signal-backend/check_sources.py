import urllib.request
import json

def check_all_sources():
    data = json.loads(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/leads').read())
    sources = {}
    for l in data['leads']:
        s = l.get('source')
        sources[s] = sources.get(s, 0) + 1
    print(f"Total Leads: {len(data['leads'])}")
    print("Sources Breakdown:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  - {src}: {count} leads")

    print("\n--- SAMPLE REDDIT LEADS ---")
    reddit_leads = [l for l in data['leads'] if l.get('source') == 'reddit']
    for r in reddit_leads[:4]:
        print(f" * [{r.get('company')}] ({r.get('country')}) - {r.get('technology')} [Score: {r.get('intentScore')}]")
        print(f"   Need: {r.get('detectedNeed')}\n")

    print("--- SAMPLE HACKERRANK LEADS ---")
    hr_leads = [l for l in data['leads'] if l.get('source') == 'hackerrank']
    for h in hr_leads[:4]:
        print(f" * [{h.get('company')}] ({h.get('country')}) - {h.get('technology')} [Score: {h.get('intentScore')}]")
        print(f"   Need: {h.get('detectedNeed')}\n")

if __name__ == '__main__':
    check_all_sources()
