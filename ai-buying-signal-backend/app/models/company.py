import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer
from app.core.database import Base

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    domain: Mapped[str | None] = mapped_column(String, nullable=True)
    industry: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    country: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    signals_count: Mapped[int] = mapped_column(Integer, default=0)
    highest_intent_score: Mapped[int] = mapped_column(Integer, default=0)
