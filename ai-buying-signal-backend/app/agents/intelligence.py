import re
import random
import os
import json
import asyncio
import logging
import hashlib
from typing import List, Dict, Any
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

groq_client = AsyncOpenAI(
    base_url=os.environ.get("FALLBACK_BASE_URL", os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")),
    api_key=os.environ.get("FALLBACK_API_KEY", os.environ.get("GROQ_API_KEY"))
)

GROQ_MODEL = os.environ.get("FALLBACK_MODEL", os.environ.get("GROQ_MODEL", "groq/compound-mini"))

# Global rate limiting and deduplication
_global_primary_semaphore = asyncio.Semaphore(1)
_lead_analysis_locks = {}
_lead_cache = {}

async def call_llm_with_fallback(messages: List[Dict[str, str]], temperature: float = 0.0, max_tokens: int = 1024, expect_json: bool = True) -> str:
    async def _call(client_to_use, model_to_use):
        response = await client_to_use.chat.completions.create(
            model=model_to_use,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM")
            
        if expect_json:
            match = re.search(r'\{.*\}', content, re.DOTALL)
            text_to_parse = match.group(0) if match else content
            try:
                json.loads(text_to_parse)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON response: {e}")
                
        return content

    result_text = None
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            async with _global_primary_semaphore:
                result_text = await _call(groq_client, GROQ_MODEL)
                await asyncio.sleep(2.5) # Throttle
            break
        except Exception as e:
            err_str = str(e)
            
            # Fail fast for hard limits like daily token limits, TPM limits, or auth errors
            if 'tokens per day' in err_str.lower() or 'tpd' in err_str.lower() or 'tpm' in err_str.lower() or 'insufficient' in err_str.lower():
                logger.warning(f"Groq Hard Limit reached: {err_str[:50]}. Instantly routing to OpenRouter Fallback...")
                break
                
            if ('429' in err_str or '413' in err_str or '502' in err_str or '503' in err_str) and attempt < max_retries - 1:
                sleep_time = (2.0 * (1.5 ** attempt)) + random.uniform(0.1, 0.5)
                logger.warning(f"Groq API Overloaded ({err_str[:20]}). Retrying in {sleep_time:.2f}s (Attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(sleep_time)
                continue
            
            # For 404 or max retries, break loop and go to fallback
            logger.warning(f"Groq API failed: {err_str}. Attempting OpenRouter Fallback...")
            break
            
    if result_text is None:
        or_key = os.environ.get("OPENROUTER_API_KEY")
        if not or_key:
            raise ValueError("Groq API failed and no OPENROUTER_API_KEY provided in .env")
        
        or_base = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        
        # A list of free OpenRouter models to try in case one is rate-limited
        free_models = [
            "google/gemma-4-31b-it:free",
            "nvidia/nemotron-3.5-lightning:free",
            "liquid/lfm-2.5-2.6b:free",
            "inclusionai/ling-3.0-flash-fin:free"
        ]
        
        user_model = os.environ.get("OPENROUTER_MODEL")
        if user_model and user_model not in free_models:
            free_models.insert(0, user_model)
            
        or_client = AsyncOpenAI(base_url=or_base, api_key=or_key)
        
        # Concurrently request all free models and return the first valid response
        async def fetch_model(model_name):
            try:
                return await _call(or_client, model_name)
            except Exception:
                return None
                
        tasks = [asyncio.create_task(fetch_model(m)) for m in free_models]
        
        while tasks:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                res = task.result()
                if res:
                    # Cancel remaining tasks since we found a valid response
                    for p in pending:
                        p.cancel()
                    return res
            # If the completed tasks failed, wait for the others
            tasks = list(pending)
            
    if not result_text:
        raise ValueError("Empty response from LLM")
        
    return result_text

class StructuredSignal(BaseModel):
    signalType: str
    businessPain: str
    technology: str
    detectedNeed: str
    explicitRequirement: bool
    intentScore: int
    iosysService: str
    aiSummary: str
    company: str
    companyConfidence: int

class IntelligencePipeline:
    def __init__(self):
        self.client = client
        
    async def analyze_signal(self, text_content: str, fallback_title: str = "") -> dict:
        cache_key = hashlib.md5((fallback_title + text_content).encode()).hexdigest()
        
        # Deduplicate simultaneous requests for the same lead
        if cache_key not in _lead_analysis_locks:
            _lead_analysis_locks[cache_key] = asyncio.Lock()
            
        async with _lead_analysis_locks[cache_key]:
            if cache_key in _lead_cache:
                return _lead_cache[cache_key]
                
            result = await self._do_analyze(text_content, fallback_title)
            _lead_cache[cache_key] = result
            return result

    async def _do_analyze(self, text_content: str, fallback_title: str) -> dict:
        system_prompt = """You are an elite B2B AI Buying Signal Analyst.
Your job is to read raw forum posts/signals and extract exactly the requested JSON payload.

CRITICAL RULES FOR EXTRACTION:
1. "intentScore": Rate 0-100 based strictly on COMMERCIAL BUYING INTENT. 
2. "signalType": Must be exactly one of: "Direct buying intent", "Vendor search", "Project intent", "Business pain", "Solution research", "Technical research", "General discussion".
3. "businessPain": Extract the actual business pain. If none exists, output exactly "Unknown". Do NOT hallucinate.
4. "detectedNeed": Extract the need. NEVER use a username, author name, company name, source name, or random word. If no need exists, output exactly "Unknown".
5. "technology": Extract the actual technologies/models mentioned (e.g. "Qwen, Gemma, Llama"). If none, output exactly "Unknown".
6. "iosysService": Match the business need to one of iOSYS's services: "Agentic AI", "Gen AI", "Web Development", "Digital Marketing", "Staffing", "Support & Maintenance", "Partnership". If there is no clear match for these services, output exactly "Unknown".
7. "aiSummary": Provide a blisteringly fast, hyper-concise 1-2 sentence summary of the opportunity.
8. "company": Extract the name of the company if mentioned. NEVER use the author's username as the company. If no company is explicitly mentioned, output exactly "Unknown".
9. "companyConfidence": Rate 0-100 on how confident you are that the extracted company name is a real company and not a username or placeholder. If company is "Unknown", output 0.
10. NEVER invent information. If there is no evidence for a field, return "Unknown" (or null/0 if boolean/integer). You must distinguish between OBSERVED facts and INFERRED assumptions. Do not invent budget or timeline.
11. Output ONLY valid JSON matching this exact structure:
{
    "signalType": "string",
    "businessPain": "string",
    "technology": "string",
    "detectedNeed": "string",
    "explicitRequirement": boolean,
    "intentScore": integer,
    "iosysService": "string",
    "aiSummary": "string",
    "company": "string",
    "companyConfidence": integer
}"""

        user_content = text_content[:500] # Cap input size to save tokens and avoid 413 errors
        print(f"Sending payload to Groq. Length of user_content: {len(user_content)}, text_content: {len(text_content)}")

        try:
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Text to analyze:\n\n{user_content}"}
            ]
            result_text = await call_llm_with_fallback(messages, temperature=0.0, max_tokens=512)
            
            match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if match:
                result_text = match.group(0)
            else:
                raise ValueError(f"No JSON object found in response: {result_text[:100]}")
                
            data = json.loads(result_text)
            
            def sanitize(val, default="Unknown"):
                if not val or str(val).strip().lower() in ["unknown", "none", "null", "not detected", "n/a", ""]:
                    return default
                return str(val).strip()

            return {
                "signalType": data.get("signalType", "General discussion"),
                "businessPain": sanitize(data.get("businessPain")),
                "technology": sanitize(data.get("technology")),
                "detectedNeed": sanitize(data.get("detectedNeed")),
                "explicitRequirement": bool(data.get("explicitRequirement", False)),
                "intentScore": int(data.get("intentScore", 0)),
                "iosysService": sanitize(data.get("iosysService")),
                "aiSummary": data.get("aiSummary", "Unable to summarize."),
                "company": sanitize(data.get("company")),
                "companyConfidence": int(data.get("companyConfidence", 0))
            }
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            
            clean_error = str(e)
            if '429' in clean_error or 'request_too_large' in clean_error or '413' in clean_error:
                clean_error = "AI Provider is currently busy or overloaded. Please try again in a few seconds."
            
            return {
                "signalType": "Question/Troubleshooting",
                "businessPain": "Unknown",
                "technology": "Unknown",
                "detectedNeed": "Unknown",
                "explicitRequirement": False,
                "intentScore": 10,
                "iosysService": "Unknown",
                "aiSummary": f"Analysis failed: {clean_error}",
                "company": "Unknown",
                "companyConfidence": 0
            }

    async def process_batch(self, raw_signals: List[Any]) -> List[dict]:
        """
        Concurrently process a batch of raw signals.
        """
        tasks = [self.analyze_signal(s.content, s.title) for s in raw_signals]
        results = await asyncio.gather(*tasks)
        return results
