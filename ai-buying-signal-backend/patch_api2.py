import sys

with open(r'C:\Users\mukee\social media listening\ai-buying-signal-backend\app\api\v1\companies.py', 'r', encoding='utf8') as f:
    lines = f.readlines()

new_func = """
def _get_realtime_search_snippets(query: str, num_results: int = 3) -> str:
    import urllib.request
    import urllib.parse
    from bs4 import BeautifulSoup
    url = f'https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
    try:
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        snippets = []
        for a in soup.find_all('a', class_='result__snippet'):
            snippets.append(a.text.strip())
            if len(snippets) >= num_results:
                break
        return "\n".join([f"- {s}" for s in snippets])
    except Exception:
        return ""

"""

# Insert function before the chat route
insert_idx = -1
for i, line in enumerate(lines):
    if "@router.post(\"/{company_id}/chat\"" in line:
        insert_idx = i
        break

if insert_idx != -1:
    lines.insert(insert_idx, new_func)
    
    # Now find the prompt and replace it
    for i in range(insert_idx, len(lines)):
        if "prompt = f\"\"\"" in lines[i]:
            # Delete the old prompt block
            end_idx = i
            while "\"\"\"" not in lines[end_idx+1]:
                end_idx += 1
            end_idx += 1
            
            # replace with new logic
            new_logic = """
    realtime_snippets = _get_realtime_search_snippets(f"{company.name} {request.message}")
    
    prompt = f\"\"\"
You are a helpful AI Sales Assistant. You are answering a salesperson's questions about the company: {company.name}.

Here is the ICP Summary & Metadata we generated: 
{analysis_json}

Here is all the raw scraped data we found on them:
{raw_context}

Here are some real-time web search results for the user's specific question:
{realtime_snippets}

Answer the user's question directly and concisely based on this information. 
Use the real-time web search results if the answer is not in the original scraped context.
\"\"\"
"""
            lines = lines[:i] + [new_logic] + lines[end_idx+1:]
            break

with open(r'C:\Users\mukee\social media listening\ai-buying-signal-backend\app\api\v1\companies.py', 'w', encoding='utf8') as f:
    f.writelines(lines)

