import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, JSON
from app.core.database import Base

class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    service_description: Mapped[str] = mapped_column(String(255))
    target_industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_geography: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    target_personas: Mapped[list[str]] = mapped_column(JSON, default=list)
    pain_points: Mapped[list[str]] = mapped_column(JSON, default=list)
    competitors: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class CampaignIntelligence(Base):
    __tablename__ = "campaign_intelligence"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id: Mapped[str] = mapped_column(String(255), index=True)
    
    positive_keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    negative_keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    buying_intent_phrases: Mapped[list[str]] = mapped_column(JSON, default=list)
    problem_phrases: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    semantic_queries: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_specific_queries: Mapped[dict] = mapped_column(JSON, default=dict) # e.g. {"reddit": ["query1"], "github": ["query2"]}
    
    icp_rules: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    model_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
