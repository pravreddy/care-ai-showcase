"""
Care AI Engine - Cache Service
Redis-backed cache for MCP tool responses.

Eliminates repeat network calls to NHS.uk.
NHS medicine pages don't change hourly — cache them for 24h.

First request:  MCP → NHS.uk (1-2 seconds) → store in Redis
Next requests:  MCP → Redis (5 milliseconds) → done

Cache stats are logged so you can see hit rates.
"""

import json
import hashlib
from typing import Optional

import redis.asyncio as redis

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("cache")

_redis_client: Optional[redis.Redis] = None

# Cache TTLs (seconds)
CACHE_TTLS = {
    "get_medicine_info": 86400,     # 24 hours — medicine pages rarely change
    "get_condition_info": 86400,    # 24 hours
    "search_nhs": 3600,            # 1 hour — search results can vary
    "get_bnf_info": 43200,         # 12 hours
    "default": 3600,               # 1 hour fallback
}

# Stats tracking
_stats = {"hits": 0, "misses": 0}


async def get_redis() -> redis.Redis:
    """Get or create the Redis connection."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection on shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


def _make_cache_key(tool_name: str, arguments: dict) -> str:
    """
    Create a deterministic cache key from tool name + arguments.
    Example: "mcp:get_medicine_info:a1b2c3d4"
    """
    args_str = json.dumps(arguments, sort_keys=True)
    args_hash = hashlib.md5(args_str.encode()).hexdigest()[:12]
    return f"mcp:{tool_name}:{args_hash}"


async def get_cached(tool_name: str, arguments: dict) -> Optional[dict]:
    """
    Check if we have a cached response for this tool call.
    Returns the cached result dict, or None if not cached.
    """
    try:
        r = await get_redis()
        key = _make_cache_key(tool_name, arguments)
        cached = await r.get(key)

        if cached:
            _stats["hits"] += 1
            logger.debug(f"Cache HIT: {tool_name} ({key})")
            return json.loads(cached)

        _stats["misses"] += 1
        logger.debug(f"Cache MISS: {tool_name} ({key})")
        return None

    except redis.ConnectionError:
        logger.warning("Redis unavailable — skipping cache read")
        return None
    except Exception as e:
        logger.warning(f"Cache read error: {e}")
        return None


async def set_cached(tool_name: str, arguments: dict, result: dict) -> None:
    """
    Cache a tool response in Redis with appropriate TTL.
    Only caches successful results.
    """
    if not result.get("success", False):
        return  # Don't cache failures

    try:
        r = await get_redis()
        key = _make_cache_key(tool_name, arguments)
        ttl = CACHE_TTLS.get(tool_name, CACHE_TTLS["default"])

        await r.setex(key, ttl, json.dumps(result))

        logger.debug(f"Cached: {tool_name} ({key}) TTL={ttl}s")

    except redis.ConnectionError:
        logger.warning("Redis unavailable — skipping cache write")
    except Exception as e:
        logger.warning(f"Cache write error: {e}")


async def invalidate(tool_name: str, arguments: dict) -> None:
    """Manually invalidate a specific cache entry."""
    try:
        r = await get_redis()
        key = _make_cache_key(tool_name, arguments)
        await r.delete(key)
        logger.info(f"Cache invalidated: {key}")
    except Exception as e:
        logger.warning(f"Cache invalidate error: {e}")


async def invalidate_all_for_tool(tool_name: str) -> int:
    """Invalidate all cached entries for a specific tool."""
    try:
        r = await get_redis()
        pattern = f"mcp:{tool_name}:*"
        keys = []
        async for key in r.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await r.delete(*keys)
        logger.info(f"Invalidated {len(keys)} cache entries for {tool_name}")
        return len(keys)
    except Exception as e:
        logger.warning(f"Cache bulk invalidate error: {e}")
        return 0


async def get_cache_stats() -> dict:
    """Get cache statistics."""
    total = _stats["hits"] + _stats["misses"]
    hit_rate = (_stats["hits"] / total * 100) if total > 0 else 0

    try:
        r = await get_redis()
        # Count cached keys
        count = 0
        async for _ in r.scan_iter(match="mcp:*"):
            count += 1

        return {
            "hits": _stats["hits"],
            "misses": _stats["misses"],
            "hit_rate_percent": round(hit_rate, 1),
            "cached_entries": count,
            "redis_connected": True,
        }
    except Exception:
        return {
            "hits": _stats["hits"],
            "misses": _stats["misses"],
            "hit_rate_percent": round(hit_rate, 1),
            "cached_entries": -1,
            "redis_connected": False,
        }
