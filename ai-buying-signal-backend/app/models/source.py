import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from app.core.database import Base

class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    tag: Mapped[str] = mapped_column(String, unique=True)
