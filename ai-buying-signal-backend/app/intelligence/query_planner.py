from typing import List, Dict
from app.models.campaign import CampaignIntelligence

class QueryPlanner:
    """
    Translates abstract Campaign Intelligence into concrete search queries for specific connectors.
    """
    
    def plan_queries(self, intelligence: CampaignIntelligence, connectors: List[str]) -> Dict[str, List[str]]:
        planned_queries = {}
        
        for connector in connectors:
            connector_queries = []
            
            # 1. Look for pre-generated source specific queries from the LLM
            if connector in intelligence.source_specific_queries:
                connector_queries.extend(intelligence.source_specific_queries[connector])
                
            # 2. Build heuristic fallback queries if none provided
            if not connector_queries:
                for target in intelligence.positive_keywords[:3]:
                    for intent in intelligence.buying_intent_phrases[:2]:
                        if connector == "reddit":
                            # E.g. (keyword1) AND (looking for)
                            connector_queries.append(f'"{target}" AND "{intent}"')
                        elif connector == "github":
                            connector_queries.append(f'{target} {intent} in:readme')
                        else:
                            connector_queries.append(f'{target} {intent}')
                            
            # 3. Deduplicate
            planned_queries[connector] = list(set(connector_queries))
            
        return planned_queries
