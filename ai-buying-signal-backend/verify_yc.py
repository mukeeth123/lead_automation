import urllib.request
import json

def verify():
    data = json.loads(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/leads').read())
    seeking_work = [l for l in data['leads'] if 'seeking work' in l.get('originalSnippet', '').lower() or 'seeking work' in l.get('company', '').lower()]
    yc_leads = [l for l in data['leads'] if l.get('source') == 'yc']
    print(f"Total Leads in API: {len(data['leads'])}")
    print(f"YC Buyer Leads: {len(yc_leads)}")
    print(f"Seeking Work (Jobseekers) remaining: {len(seeking_work)}")
    print("\nSample Real YC Buyer Leads:")
    for y in yc_leads[:6]:
        print(f" - [{y.get('company')}] ({y.get('country')}): {y.get('aiSummary')[:80]}... (Score: {y.get('intentScore')})")

if __name__ == '__main__':
    verify()
