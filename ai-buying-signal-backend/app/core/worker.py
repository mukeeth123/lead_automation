import asyncio
from typing import Any, Dict
from app.core.redis import get_redis_settings
from app.core.database import AsyncSessionLocal
from app.models.discovery_job import DiscoveryJob
from app.connectors.reddit import RedditConnector

async def startup(ctx: Dict[Any, Any]) -> None:
    """Initialize resources for the worker."""
    ctx["db_session"] = AsyncSessionLocal()

async def shutdown(ctx: Dict[Any, Any]) -> None:
    """Cleanup resources."""
    await ctx["db_session"].close()

async def run_discovery_job(ctx: Dict[Any, Any], job_id: str, campaign_id: str) -> str:
    """
    Background task to run discovery across connectors.
    """
    db = ctx["db_session"]
    
    # 1. We would normally fetch the campaign and select connectors
    # For now, we just use the RedditConnector MVP
    connector = RedditConnector()
    
    signals_discovered = 0
    try:
        async with connector:
            # Check rate limit and health before proceeding
            is_healthy = await connector.health_check()
            if not is_healthy:
                return f"Source {connector.source_name} is unhealthy."
                
            raw_events = await connector.discover(campaign=None)
            signals_discovered = len(raw_events)
            
            # Here we would save raw_events to the DB and queue them for processing
            # ...
            
    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        return "failed"
        
    return f"completed - discovered {signals_discovered} raw signals"

class WorkerSettings:
    functions = [run_discovery_job]
    redis_settings = get_redis_settings()
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10
