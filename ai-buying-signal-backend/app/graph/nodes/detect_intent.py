import json
from pydantic import BaseModel
from app.agents.intelligence import call_llm_with_fallback
from app.graph.state import AgentState

async def detect_intent(state: AgentState) -> dict:
    """Node to rigorously classify the intent of a post to find genuine buyers."""
    raw_signal = state.get("raw_signal", {})
    text_content = raw_signal.get("content", "")
    title = raw_signal.get("title", "")
    
    full_text = f"{title}\n\n{text_content}"
    
    prompt = f"""
You are an elite B2B Intent Detection Engine. Your sole purpose is to analyze social media and forum posts to discover ACTUAL POSTS where a person or company is ACTIVELY LOOKING for a product, service, expert, agency, developer, consultant, or solution.

A post should NOT become a qualified lead simply because it contains keywords such as "AI", "developer", "automation", "marketing", or "software".

Required Classification Categories:
1. EXPLICIT_BUYING_INTENT ("Looking for an AI development company", "Need someone to build an MVP")
2. RECOMMENDATION_SEEKING ("Can anyone recommend a good digital marketing agency?")
3. HIRING_INTENT ("Looking to hire an AI automation expert")
4. VENDOR_SWITCHING ("Our current agency is failing. Looking for a replacement.")
5. PROBLEM_SEEKING_SOLUTION ("Our manual processes are taking too much time. What solution should we use?")
6. GENERAL_DISCUSSION ("AI is changing the future", "I built an AI agent")
7. EDUCATIONAL_CONTENT ("Here is how to learn software development")
8. NEWS_OR_INFORMATION ("Company X launched a new product")
9. NOT_RELEVANT

CORE RULE:
Is the author of this post actively looking for a solution, service provider, vendor, expert, agency, developer, consultant, or recommendation?
If they fall into categories 1 through 5, `is_buying_signal` MUST be true.
If they fall into categories 6 through 9, `is_buying_signal` MUST be false.

Analyze the following text:
{full_text[:2000]}

Return ONLY valid JSON matching this exact schema:
{{
  "is_buying_signal": true/false,
  "intent_category": "One of the 9 categories",
  "intent_confidence": 0.0 to 1.0,
  "what_they_are_looking_for": "Brief string or null",
  "problem_detected": "Brief description of their pain point or null",
  "urgency": "HIGH/MEDIUM/LOW or null",
  "author_type": "INDIVIDUAL/BUSINESS/UNKNOWN",
  "reason": "Detailed explanation of why this categorization was made"
}}
"""
    
    try:
        messages = [{"role": "user", "content": prompt}]
        result_text = await call_llm_with_fallback(messages, temperature=0.0, expect_json=True)
        data = json.loads(result_text)
        
        return {
            "is_buying_signal": bool(data.get("is_buying_signal", False)),
            "intent_category": data.get("intent_category", "UNKNOWN"),
            "intent_confidence": float(data.get("intent_confidence", 0.0)),
            "what_they_are_looking_for": data.get("what_they_are_looking_for"),
            "problem_detected": data.get("problem_detected"),
            "urgency": data.get("urgency"),
            "author_type": data.get("author_type"),
            "reason": data.get("reason")
        }
    except Exception as e:
        return {
            "is_buying_signal": False,
            "intent_category": "ERROR",
            "reason": f"Failed to detect intent: {str(e)}",
            "errors": state.get("errors", []) + [f"Detect intent failed: {e}"]
        }
