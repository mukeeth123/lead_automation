import json

with open('Untitled41 (1).ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

with open('notebook_summary.md', 'w', encoding='utf-8') as out:
    for i, cell in enumerate(nb.get('cells', [])):
        if cell['cell_type'] == 'code':
            out.write(f"### Cell {i}\n")
            for output in cell.get('outputs', []):
                if 'text' in output:
                    text = "".join(output['text'])
                    if 'http' in text or 'Total' in text or 'success' in text.lower():
                        out.write("```\n" + text[:2000] + "\n```\n")
                elif 'data' in output and 'text/plain' in output['data']:
                    text = "".join(output['data']['text/plain'])
                    if 'http' in text or 'Total' in text or 'success' in text.lower():
                        out.write("```\n" + text[:2000] + "\n```\n")
