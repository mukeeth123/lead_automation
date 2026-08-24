import os
import json
import asyncio
import logging
from typing import List, Dict, Any
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Initialize Groq client using OpenAI SDK format
client = AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY")
)

# Use robust model for intelligence extraction
MODEL_NAME = "mixtral-8x7b-32768"

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
        self.semaphore = asyncio.Semaphore(5)  # Concurrency limit to avoid rate limiting
        
    async def analyze_signal(self, text_content: str, fallback_title: str = "") -> dict:
        """
        Analyze a raw signal and extract structured B2B buying intelligence.
        """
        system_prompt = """You are an elite B2B AI Buying Signal Analyst.
Your job is to read raw forum posts/signals and extract exactly the requested JSON payload.

Rules:
1. "intentScore": Rate 0-100 based on the leads requirement. 
   - 90-100: Explicitly hiring, buying, or desperate for a solution.
   - 70-89: Clear pain point with a high likelihood they need help.
   - 40-69: Asking for troubleshooting, tutorials, or general tech discussion.
   - 0-39: Random news, announcements, or unrelated.
2. "aiSummary": Provide a blisteringly fast, hyper-concise 1-2 sentence summary of the opportunity.
3. Keep all text fields as short as possible to save tokens.
4. Output ONLY valid JSON matching this exact structure:
{
    "signalType": "string",
    "businessPain": "short string",
    "technology": "string",
    "detectedNeed": "string",
    "explicitRequirement": boolean,
    "intentScore": integer,
    "iosysService": "string",
    "aiSummary": "string"
}"""

        user_content = text_content[:2000] # Cap input size to save tokens and speed up inference

        try:
            async with self.semaphore:
                response = await self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Text to analyze:\n\n{user_content}"}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=256 # Constrain output tokens for blazing fast response
                )
                
                result_text = response.choices[0].message.content
                if not result_text:
                    raise ValueError("Empty response from LLM")
                    
                data = json.loads(result_text)
                
                # Default mapping logic for safety, ensuring schema compliance
                return {
                    "signalType": data.get("signalType", "Unknown"),
                    "businessPain": data.get("businessPain", "Unknown"),
                    "technology": data.get("technology", "Unknown"),
                    "detectedNeed": data.get("detectedNeed", fallback_title),
                    "explicitRequirement": bool(data.get("explicitRequirement", False)),
                    "intentScore": int(data.get("intentScore", 0)),
                    "iosysService": data.get("iosysService", "Software Consulting"),
                    "aiSummary": data.get("aiSummary", "Unable to summarize.")
                }
                
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            # Fast, robust fallback if parsing fails
            return {
                "signalType": "Question/Troubleshooting",
                "businessPain": "Unknown",
                "technology": "Unknown",
                "detectedNeed": fallback_title,
                "explicitRequirement": False,
                "intentScore": 10,
                "iosysService": "Unknown",
                "aiSummary": text_content[:100] + "..."
            }

    async def process_batch(self, raw_signals: List[Any]) -> List[dict]:
        """
        Concurrently process a batch of raw signals.
        """
        tasks = [self.analyze_signal(s.content, s.title) for s in raw_signals]
        results = await asyncio.gather(*tasks)
        return results
