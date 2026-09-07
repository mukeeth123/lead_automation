import os
import glob
import re

agent_dir = "c:/Users/mukee/social media listening/ai-buying-signal-backend/app/agents"
agent_files = glob.glob(f"{agent_dir}/**/agent.py", recursive=True)

for file in agent_files:
    if "wellfound" in file:
        # Wellfound is entirely mock, so we just make it return empty
        with open(file, "w", encoding="utf-8") as f:
            f.write('''from datetime import datetime, timezone
import time
from app.schemas.signal import RawSignalCreate

class WellfoundAgent:
    def __init__(self):
        pass

    async def collect(self):
        return []
''')
        print(f"Cleared Wellfound: {file}")
        continue
        
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Match from "if len(signals) <" up to "return signals"
    new_content = re.sub(r'([ \t]+)if len\(signals\) < \d+:.*?(return signals)', r'\1\2', content, flags=re.DOTALL)
    
    if new_content != content:
        with open(file, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Cleaned mocks from: {file}")
    else:
        # Nitter doesn't have if len(signals) <, it just returns mock. Let's fix Nitter specifically
        if "nitter" in file:
            nitter_clean = re.sub(r'import hashlib\s+mock_tweets = \[.*?\].*?signals\.append\(.*?\)\)\n', '', content, flags=re.DOTALL)
            with open(file, "w", encoding="utf-8") as f:
                f.write(nitter_clean)
            print(f"Cleaned Nitter: {file}")
