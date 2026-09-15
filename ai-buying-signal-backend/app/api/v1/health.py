import time
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter()
startup_time = time.time()

@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    uptime = time.time() - startup_time
    return {
        "status": "healthy",
        "uptime_seconds": round(uptime, 2)
    }

@router.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
