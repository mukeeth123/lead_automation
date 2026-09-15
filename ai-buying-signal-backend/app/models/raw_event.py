import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, JSON
from app.core.database import Base

class RawEvent(Base):
    __tablename__ = "raw_events"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_name: Mapped[str] = mapped_column(String(255), index=True)
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    raw_payload: Mapped[dict] = mapped_column(JSON)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    connector_version: Mapped[str] = mapped_column(String(255), default="1.0")
    processing_status: Mapped[str] = mapped_column(String(255), default="PENDING", index=True)
    error_information: Mapped[dict | None] = mapped_column(JSON, nullable=True)
