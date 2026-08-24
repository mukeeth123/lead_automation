import json, re
with open('Untitled41 (1).ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)
for c in nb['cells']:
    lower_c = str(c).lower()
    if 'reddit' in lower_c or 'contractsfinder' in lower_c or 'contract' in lower_c:
        matches = re.findall(r'https?://[^\s"\'\\]+', str(c))
        if matches:
            print("Found:", matches)
