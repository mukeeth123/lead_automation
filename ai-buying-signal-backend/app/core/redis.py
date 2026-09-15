from arq.connections import RedisSettings
from app.core.config import settings

def get_redis_settings() -> RedisSettings:
    # Basic parsing of redis://localhost:6379/0
    # In production, use proper URL parsing
    host = "localhost"
    port = 6379
    if settings.REDIS_URL.startswith("redis://"):
        parts = settings.REDIS_URL.replace("redis://", "").split(":")
        if len(parts) == 2:
            host = parts[0]
            port = int(parts[1].split("/")[0])
    
    return RedisSettings(host=host, port=port)
