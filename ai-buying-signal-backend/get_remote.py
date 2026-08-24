import json, re
with open('Untitled41 (1).ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)
for c in nb['cells']:
    if 'remote' in str(c).lower():
        matches = re.findall(r'https?://[^\s"\'\\]+remote[^\s"\'\\]+', str(c))
        if matches:
            print(matches)
