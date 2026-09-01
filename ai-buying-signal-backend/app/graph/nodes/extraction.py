import re
import json
import logging
from app.graph.state import AgentState
from app.agents.intelligence import call_llm_with_fallback

logger = logging.getLogger(__name__)

async def extract_all(state: AgentState) -> AgentState:
    raw = state.get("raw_signal", {})
    title = raw.get("title", "")
    content = raw.get("content", "")
    author = raw.get("author", "Unknown")
    source = raw.get("source", "Unknown")
    
    inferred_profile = "Unknown"
    if author != "Unknown":
        if source == "github": inferred_profile = f"https://github.com/{author}"
        elif source == "reddit": inferred_profile = f"https://reddit.com/user/{author}"
        elif source == "hackernews": inferred_profile = f"https://news.ycombinator.com/user?id={author}"
        elif source == "n8n": inferred_profile = f"https://community.n8n.io/u/{author}"
    
    system_prompt = f"""You are an elite B2B AI Buying Signal Qualifier and Intelligence Extractor.
Analyze the following post and extract comprehensive intelligence in a single JSON payload.

Context info:
Author: {author}
Source: {source}
Author's Base Profile URL (Inferred): {inferred_profile}

RULES:
1. is_qualified: true if it involves a clear business need, pain point, or an explicit request for help/services. Simple mentions of AI, APIs, or general technical discussions are NOISE (is_qualified: false).
2. DO NOT output "Unknown" or "None" for ANY of the core opportunity fields (business_pain, detected_need, technology, buying_stage, service_fit, recommended_action, ai_summary). You MUST infer and generate a highly educated guess for these based on the context.
3. ANTI-HALLUCINATION FOR CONTACTS & URLS: 
   - NEVER guess or invent company websites (e.g. company.com). Only extract it if explicitly mentioned in the text or derived from an explicitly provided email domain.
   - NEVER guess or invent social profiles (like linkedin.com/in/name or twitter.com/name). Only extract profiles if the exact handle (e.g., @username) or URL is explicitly provided in the text.
   - If contact info or websites are not explicitly provided, you MUST output "Unknown".

Output strictly valid JSON with this exact structure:
{{
    "is_qualified": boolean,
    "qualification_reason": "string explaining why",
    "noise_level": "High" | "Medium" | "Low",
    "company_name": "string (extract company if mentioned, else Unknown)",
    "company_website": "string (infer website from company name, else Unknown)",
    "industry": "string (Infer the industry based on context, e.g. SaaS, Healthcare, Finance, E-commerce, Marketing. If completely unknown, guess Software)",
    "region": "string (extract or infer region, else Unknown)",
    "business_pain": "string (Infer the core problem they are facing. Do not use Unknown)",
    "detected_need": "string (Infer what they need to solve the pain. Do not use Unknown)",
    "technology": "string (Extract or guess the relevant tech stack. Do not use Unknown)",
    "buying_stage": "string (Infer either Researching, Evaluating, or Ready to Buy. Never output Unknown)",
    "service_fit": "string (Determine the exact service they need, e.g. Custom AI Agents, Automation Setup, Staff Augmentation. Never output Unknown)",
    "recommended_action": "string (Provide a specific, actionable next step. Never output Unknown)",
    "evidence": ["evidence 1", "evidence 2"],
    "ai_summary": "string (Dense 3-bullet summary: 1. Core pain, 2. Current tech, 3. Exact need. Use telegraphic style, omit filler words to save tokens. NEVER output Unknown)",
    "intent_score": integer (0-100),
    "confidence_score": integer (0-100, confidence in company identity),
    "email": "string or Unknown",
    "phone_number": "string or Unknown",
    "source_profile_url": "string or Unknown",
    "contact_page": "string or Unknown",
    "github_profile": "string or Unknown",
    "twitter_profile": "string or Unknown",
    "linkedin_profile": "string or Unknown",
    "other_profiles": ["string"],
    "contact_confidence": integer (0-100),
    "contact_verification": "string"
}}
"""
    
    text_to_analyze = f"Title: {title}\nContent: {content[:1500]}"
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text_to_analyze}
        ]
        result_text = await call_llm_with_fallback(messages, temperature=0.0)
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if match:
            result = json.loads(match.group(0))
        else:
            result = json.loads(result_text)
            
        # Map ALL extracted fields back to state
        for k in ["is_qualified", "qualification_reason", "noise_level", "company_name", 
                  "company_website", "industry", "region", "business_pain", "detected_need", "technology", 
                  "buying_stage", "service_fit", "recommended_action", "ai_summary", "email", 
                  "phone_number", "contact_page", "github_profile", "twitter_profile", 
                  "linkedin_profile", "contact_verification"]:
            if k in result:
                state[k] = result[k]
                
        state["evidence"] = result.get("evidence", [])
        state["other_profiles"] = result.get("other_profiles", [])
        
        state["intent_score"] = int(result.get("intent_score", 0))
        state["confidence_score"] = int(result.get("confidence_score", 0))
        state["contact_confidence"] = int(result.get("contact_confidence", 0))
        
        sp_url = result.get("source_profile_url", "Unknown")
        if sp_url == "Unknown" and inferred_profile != "Unknown":
            sp_url = inferred_profile
        state["source_profile_url"] = sp_url
        
    except Exception as e:
        logger.error(f"Unified extraction failed: {e}")
        state["is_qualified"] = False
        state["qualification_reason"] = f"Error: {str(e)}"
        
    return state
