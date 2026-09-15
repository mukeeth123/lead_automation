import json
from app.agents.intelligence import call_llm_with_fallback
from app.models.campaign import Campaign, CampaignIntelligence

class CampaignIntelligenceGenerator:
    async def generate_intelligence(self, campaign: Campaign) -> CampaignIntelligence:
        prompt = f"""
You are an expert AI Marketing Strategist. Analyze the following Campaign and generate precise intelligence data.

Campaign Name: {campaign.name}
Service Description: {campaign.service_description}
Target Industry: {campaign.target_industry}
Target Geography: {campaign.target_geography}
Target Personas: {campaign.target_personas}

Return ONLY valid JSON in this exact structure, with no markdown wrappers:
{{
    "positive_keywords": ["keyword1", "keyword2"],
    "negative_keywords": ["noise1", "noise2"],
    "buying_intent_phrases": ["looking for an agency", "need a developer"],
    "problem_phrases": ["system is slow", "can't hire fast enough"],
    "semantic_queries": ["We need to rebuild our legacy application", "Looking to augment our IT staff"],
    "source_specific_queries": {{
        "reddit": ["flair_name:\\\"Hiring\\\" AND \\\"development\\\""],
        "github": ["language:python looking for maintainer"]
    }},
    "icp_rules": ["Company must be B2B", "Excludes consumer brands"]
}}
        """
        
        messages = [{"role": "system", "content": prompt}]
        
        try:
            result_text = await call_llm_with_fallback(messages, temperature=0.2, max_tokens=1024, expect_json=True)
            data = json.loads(result_text)
            
            return CampaignIntelligence(
                campaign_id=campaign.id,
                positive_keywords=data.get("positive_keywords", []),
                negative_keywords=data.get("negative_keywords", []),
                buying_intent_phrases=data.get("buying_intent_phrases", []),
                problem_phrases=data.get("problem_phrases", []),
                semantic_queries=data.get("semantic_queries", []),
                source_specific_queries=data.get("source_specific_queries", {}),
                icp_rules=data.get("icp_rules", [])
            )
        except Exception as e:
            print(f"Error generating campaign intelligence: {e}")
            raise
