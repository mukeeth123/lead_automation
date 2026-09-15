import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Float, Integer
from app.core.database import Base

class SourceHealth(Base):
    __tablename__ = "source_health"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    
    status: Mapped[str] = mapped_column(String(255), default="HEALTHY") # HEALTHY, DEGRADED, OFFLINE
    success_rate: Mapped[float] = mapped_column(Float, default=100.0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    rate_limit_hits: Mapped[int] = mapped_column(Integer, default=0)
    
    last_successful_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
