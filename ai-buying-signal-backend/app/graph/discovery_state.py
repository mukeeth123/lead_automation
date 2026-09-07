from typing import TypedDict, Optional, List, Dict, Any, Annotated
import operator

class LeadDiscoveryState(TypedDict):
    # Discovery phase
    industry: str
    service: str
    icp: str
    keywords: List[str]
    search_queries: List[str]
    
    # URL collection
    discovered_urls: Annotated[List[Dict[str, Any]], operator.add]
    deduplicated_urls: List[Dict[str, Any]]
    
    # Batch processing
    current_url_index: int
    current_url_data: Optional[Dict[str, Any]]
    
    # Crawling & Extraction
    selected_crawler: str # 'scrapy', 'crawlee', 'playwright'
    extraction_failed: bool
    retry_count: int
    extracted_content: Optional[str]
    
    # Qualification
    is_qualified: bool
    tier: Optional[str]
    score: int
    qualification_breakdown: List[str]
    
    # Enrichment
    enriched_company_info: Optional[Dict[str, Any]]
    
    # Output / Final
    saved_leads: Annotated[List[Dict[str, Any]], operator.add]
    errors: Annotated[List[str], operator.add]
