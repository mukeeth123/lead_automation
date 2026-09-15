from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from app.core.config import settings

class Base(DeclarativeBase):
    pass

async_engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

sync_url = settings.DATABASE_URL.replace("+asyncpg", "").replace("+aiosqlite", "").replace("+aiomysql", "+pymysql")
sync_engine = create_engine(sync_url, echo=False)

from sqlalchemy.orm import sessionmaker
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def get_db():
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
