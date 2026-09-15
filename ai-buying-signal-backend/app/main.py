from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.leads import router as leads_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.metadata import router as metadata_router

app = FastAPI(title="AI Buying Signal Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leads_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1/analytics")
app.include_router(metadata_router, prefix="/api/v1/metadata")
from app.api.v1.campaigns import router as campaigns_router
from app.api.v1.health import router as health_router
from app.api.v1.services import router as services_router
from app.core.logging import setup_logging_and_tracing

# Initialize Observability
setup_logging_and_tracing()

app.include_router(campaigns_router, prefix="/api/v1/campaigns")
app.include_router(services_router, prefix="/api/v1")
app.include_router(health_router)
