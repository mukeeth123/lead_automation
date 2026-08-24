import httpx
res = httpx.get('http://127.0.0.1:8000/api/v1/leads')
print('Remote OK count:', sum(1 for i in res.json() if i.get('source') == 'remote_ok'))
