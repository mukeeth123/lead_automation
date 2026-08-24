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

client = AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY")
)

MODEL_NAME = "groq/compound-mini"

# Global rate limiting and deduplication
_global_groq_semaphore = asyncio.Semaphore(1)
_lead_analysis_locks = {}
_lead_cache = {}

class StructuredSignal(BaseModel):
    signalType: str
    businessPain: str
    technology: str
    detectedNeed: str
    explicitRequirement: bool
    intentScore: int
    iosysService: str
    aiSummary: str

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
   - 90-100: Explicitly hiring, buying, or desperate for a commercial solution.
   - 70-89: Clear business pain point with a high likelihood they need external help.
   - 30-69: Technical research, benchmarking, tutorials, or open-source discussion. (Do not over-score technical benchmarking. Typically 30-40).
   - 0-29: Random news, announcements, or unrelated.
2. "signalType": Must be exactly one of: "Direct buying intent", "Vendor search", "Project intent", "Business pain", "Solution research", "Technical research", "General discussion".
3. "businessPain": Extract the actual business pain. If none exists, output exactly "Not detected". Do NOT hallucinate or output "Unknown".
4. "detectedNeed": Extract the need. NEVER use a username, author name, company name, source name, or random word. If no need exists, output exactly "Not detected".
5. "technology": Extract the actual technologies/models mentioned (e.g. "Qwen, Gemma, Llama"). If none, output exactly "Not detected".
6. "iosysService": Match the business need to one of iOSYS's services: "Agentic AI", "Gen AI", "Web Development", "Digital Marketing", "Staffing", "Support & Maintenance", "Partnership". If there is no clear match for these services, output exactly "Not detected".
7. "aiSummary": Provide a blisteringly fast, hyper-concise 1-2 sentence summary of the opportunity.
8. NEVER invent information. If there is no evidence for a field, return "Not detected" (or null if boolean/integer).
9. Output ONLY valid JSON matching this exact structure:
{
    "signalType": "string",
    "businessPain": "string",
    "technology": "string",
    "detectedNeed": "string",
    "explicitRequirement": boolean,
    "intentScore": integer,
    "iosysService": "string",
    "aiSummary": "string"
}"""

        user_content = text_content[:500] # Cap input size to save tokens and avoid 413 errors
        print(f"Sending payload to Groq. Length of user_content: {len(user_content)}, text_content: {len(text_content)}")

        async def _call_llm(client_to_use, model_to_use):
            response = await client_to_use.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Text to analyze:\n\n{user_content}"}
                ],
                temperature=0.0,
                max_tokens=512
            )
            return response.choices[0].message.content

        try:
            result_text = None
            max_retries = 3
            
            # Primary Service (Groq)
            for attempt in range(max_retries):
                try:
                    async with _global_groq_semaphore:
                        result_text = await _call_llm(self.client, MODEL_NAME)
                        await asyncio.sleep(2.5) # Throttle
                    break
                except Exception as e:
                    err_str = str(e)
                    if ('429' in err_str or '413' in err_str or '502' in err_str or '503' in err_str) and attempt < max_retries - 1:
                        sleep_time = (2.0 * (1.5 ** attempt)) + random.uniform(0.1, 0.5)
                        logger.warning(f"Groq API Overloaded ({err_str[:20]}). Retrying in {sleep_time:.2f}s (Attempt {attempt+1}/{max_retries})")
                        await asyncio.sleep(sleep_time)
                        continue
                    elif attempt == max_retries - 1:
                        logger.warning("Primary API failed after retries. Attempting Fallback Service...")
                        break
                    raise e
            
            # Fallback Service
            if result_text is None:
                fallback_key = os.environ.get("FALLBACK_API_KEY")
                if not fallback_key:
                    raise ValueError("Groq API rate limit exceeded and no FALLBACK_API_KEY provided in .env")
                
                fallback_base = os.environ.get("FALLBACK_BASE_URL", "https://api.openai.com/v1")
                fallback_model = os.environ.get("FALLBACK_MODEL", "gpt-4o-mini")
                
                fallback_client = AsyncOpenAI(base_url=fallback_base, api_key=fallback_key)
                
                logger.info(f"Using fallback model: {fallback_model} at {fallback_base}")
                result_text = await _call_llm(fallback_client, fallback_model)
                
            if not result_text:
                raise ValueError("Empty response from LLM")
            
            match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if match:
                result_text = match.group(0)
            else:
                raise ValueError(f"No JSON object found in response: {result_text[:100]}")
                
            data = json.loads(result_text)
            
            def sanitize(val, default="Not detected"):
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
                "aiSummary": data.get("aiSummary", "Unable to summarize.")
            }
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            
            clean_error = str(e)
            if '429' in clean_error or 'request_too_large' in clean_error or '413' in clean_error:
                clean_error = "AI Provider is currently busy or overloaded. Please try again in a few seconds."
            
            return {
                "signalType": "Question/Troubleshooting",
                "businessPain": "Not detected",
                "technology": "Not detected",
                "detectedNeed": "Not detected",
                "explicitRequirement": False,
                "intentScore": 10,
                "iosysService": "Not detected",
                "aiSummary": f"Analysis failed: {clean_error}"
            }

    async def process_batch(self, raw_signals: List[Any]) -> List[dict]:
        """
        Concurrently process a batch of raw signals.
        """
        tasks = [self.analyze_signal(s.content, s.title) for s in raw_signals]
        results = await asyncio.gather(*tasks)
        return results
