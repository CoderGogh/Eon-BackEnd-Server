import json
from typing import Any, Optional
from redis.asyncio import Redis
from .core.config import settings

redis_pool: Optional[Redis] = None


async def init_redis_pool():
    global redis_pool
    try:
        redis_pool = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            password=settings.REDIS_PASSWORD or None,
            decode_responses=True,
        )
        await redis_pool.ping()
        try:
            info = await redis_pool.info()
            print(f"Redis connected ({settings.REDIS_HOST}:{settings.REDIS_PORT}) role={info.get('role')} clients={info.get('connected_clients')} mem={info.get('used_memory_human')}")
        except Exception:
            print(f"Redis connected ({settings.REDIS_HOST}:{settings.REDIS_PORT})")
    except Exception as e:
        print(f"Redis connection failed ({settings.REDIS_HOST}:{settings.REDIS_PORT}): {e}")
        redis_pool = None


async def get_redis_info() -> dict:
    """디버깅용 Redis INFO 요약 반환 (best-effort)."""
    if redis_pool is None:
        return {"ok": False, "error": "no_redis_client"}
    try:
        info = await redis_pool.info()
        return {
            "ok": True,
            "role": info.get("role"),
            "used_memory_human": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def close_redis_pool():
    global redis_pool
    if redis_pool:
        await redis_pool.close()
        redis_pool = None


async def get_redis_client() -> Optional[Redis]:
    return redis_pool


async def get_cache(key: str, client: Optional[Redis] = None) -> Any:
    current_client = client or redis_pool
    if current_client is None:
        return None
    data = await current_client.get(key)
    return json.loads(data) if data else None


async def set_cache(key: str, value: Any, expire: int = settings.CACHE_EXPIRE_SECONDS, client: Optional[Redis] = None):
    current_client = client or redis_pool
    if current_client is None:
        return
    await current_client.set(key, json.dumps(value, default=str), ex=expire)


async def delete_cache(key: str):
    if redis_pool:
        await redis_pool.delete(key)
