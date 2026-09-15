import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, JSON, ForeignKey
from app.core.database import Base

class UnifiedSignalModel(Base):
    __tablename__ = "unified_signals"

    signal_id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String(255), index=True)
    source_type: Mapped[str] = mapped_column(String(255), index=True)
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    external_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    campaign_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    
    content: Mapped[dict] = mapped_column(JSON)
    author: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    language: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    raw_event_id: Mapped[str] = mapped_column(ForeignKey("raw_events.id"), index=True)
    
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    
    content_hash: Mapped[str] = mapped_column(String(255), index=True)
    
    # pgvector embedding for semantic search
    from sqlalchemy.types import TypeDecorator, String
    import os
    
    class VectorFallback(TypeDecorator):
        impl = String
        cache_ok = True
        
        def load_dialect_impl(self, dialect):
            if dialect.name == 'postgresql':
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(384))
            from sqlalchemy import Text
            return dialect.type_descriptor(Text())

    embedding = mapped_column(VectorFallback(), nullable=True) # 384 for lightweight models
