from langgraph.graph import StateGraph, END
from app.graph.discovery_state import LeadDiscoveryState
from app.graph.nodes.discovery import generate_queries, discover_searxng, merge_and_deduplicate
from app.graph.nodes.crawling import select_crawler, extract_content_scrapy, extract_content_playwright, validate_content, prepare_next_url
from app.graph.nodes.qualification import qualify_lead, enrich_lead, save_lead, increment_url_index

def route_crawler(state: LeadDiscoveryState):
    if state.get("selected_crawler") == "playwright":
        return "extract_playwright"
    return "extract_scrapy"

def route_validation(state: LeadDiscoveryState):
    if state.get("extraction_failed"):
        # If we failed on scrapy and haven't retried yet, route back to select_crawler for escalation
        if state.get("retry_count", 0) <= 1 and state.get("selected_crawler") == "scrapy":
            return "select_crawler"
        else:
            # Drop the URL
            return "increment_url"
    return "qualify_lead"

def route_qualification(state: LeadDiscoveryState):
    if state.get("is_qualified"):
        return "enrich_lead"
    return "increment_url"

def route_batch(state: LeadDiscoveryState):
    idx = state.get("current_url_index", 0)
    urls = state.get("deduplicated_urls", [])
    if idx < len(urls):
        return "prepare_next_url"
    return END

def route_prepare_next(state: LeadDiscoveryState):
    if state.get("current_url_data") is None:
        return END
    return "select_crawler"

# Build the Graph
workflow = StateGraph(LeadDiscoveryState)

# Discovery Phase
workflow.add_node("generate_queries", generate_queries)
workflow.add_node("discover_searxng", discover_searxng)
workflow.add_node("merge_and_deduplicate", merge_and_deduplicate)

# Batch Processing
workflow.add_node("prepare_next_url", prepare_next_url)
workflow.add_node("select_crawler", select_crawler)
workflow.add_node("extract_scrapy", extract_content_scrapy)
workflow.add_node("extract_playwright", extract_content_playwright)
workflow.add_node("validate_content", validate_content)

# Qualification
workflow.add_node("qualify_lead", qualify_lead)
workflow.add_node("enrich_lead", enrich_lead)
workflow.add_node("save_lead", save_lead)
workflow.add_node("increment_url", increment_url_index)

# Define Edges
workflow.set_entry_point("generate_queries")
workflow.add_edge("generate_queries", "discover_searxng")

workflow.add_edge("discover_searxng", "merge_and_deduplicate")

workflow.add_edge("merge_and_deduplicate", "prepare_next_url")

workflow.add_conditional_edges("prepare_next_url", route_prepare_next)

workflow.add_conditional_edges("select_crawler", route_crawler)

workflow.add_edge("extract_scrapy", "validate_content")
workflow.add_edge("extract_playwright", "validate_content")

workflow.add_conditional_edges("validate_content", route_validation)

workflow.add_conditional_edges("qualify_lead", route_qualification)

workflow.add_edge("enrich_lead", "save_lead")
workflow.add_edge("save_lead", "increment_url")

workflow.add_conditional_edges("increment_url", route_batch)

discovery_graph = workflow.compile()
