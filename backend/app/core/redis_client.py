"""
app/core/redis_client.py — Async Redis connection.
"""
from __future__ import annotations

import redis.asyncio as redis
import structlog

from app.config import get_settings

settings = get_settings()
log = structlog.get_logger("redis")

class RedisClient:
    def __init__(self):
        self.pool = None
        self.client: redis.Redis | None = None

    async def connect(self):
        self.pool = redis.ConnectionPool.from_url(settings.redis_url, decode_responses=True)
        self.client = redis.Redis(connection_pool=self.pool)
        try:
            await self.client.ping()
            log.info("redis_connected")
        except Exception as e:
            log.warning("redis_connection_failed", error=str(e))

    async def disconnect(self):
        if self.pool:
            await self.pool.disconnect()
            log.info("redis_disconnected")

    async def get(self, key: str) -> str | None:
        if not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception:
            return None

    async def set(self, key: str, value: str, expire: int = None):
        if not self.client:
            return
        try:
            await self.client.set(key, value, ex=expire)
        except Exception:
            pass

redis_client = RedisClient()
