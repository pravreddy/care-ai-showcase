"""
Care AI Engine - Health Check Routes v2
Checks MCP connectivity, LLM availability, and NHS data access.
"""

import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import get_session_factory
from app.models.schemas import HealthResponse
from app.mcp.client.mcp_client import mcp_client
from app.services.llm_service import llm_service
from app.services import cache_service
from app.core.logging import get_logger

logger = get_logger("api.health")

router = APIRouter(tags=["Health"])

_start_time = time.monotonic()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Comprehensive health check for all services.
    Used by load balancers, Docker health checks, and monitoring.
    """
    settings = get_settings()

    services = {}

    # Check MCP tools
    try:
        tools = mcp_client.available_tools
        services["mcp"] = f"healthy ({len(tools)} tools registered)"
    except Exception as e:
        services["mcp"] = f"unhealthy: {str(e)[:100]}"

    # Check NHS connectivity (quick test)
    try:
        result = await mcp_client.call_tool(
            "get_medicine_info", {"medicine_name": "paracetamol"}
        )
        if result.get("success"):
            services["nhs_data"] = "healthy (live connection)"
        else:
            services["nhs_data"] = "degraded (NHS not responding)"
    except Exception as e:
        services["nhs_data"] = f"unhealthy: {str(e)[:100]}"

    # Check Ollama/LLM
    try:
        llm_ok = await llm_service.health_check()
        services["ollama"] = "healthy" if llm_ok else "model not loaded"
    except Exception as e:
        services["ollama"] = f"unhealthy: {str(e)[:100]}"

    # Check Redis cache
    try:
        stats = await cache_service.get_cache_stats()
        if stats["redis_connected"]:
            services["redis_cache"] = (
                f"healthy ({stats['cached_entries']} entries, "
                f"{stats['hit_rate_percent']}% hit rate)"
            )
        else:
            services["redis_cache"] = "degraded (not connected)"
    except Exception as e:
        services["redis_cache"] = f"unhealthy: {str(e)[:100]}"

    # Overall status
    all_healthy = all("healthy" in v for v in services.values())

    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        version=settings.app_version,
        services=services,
        uptime_seconds=round(time.monotonic() - _start_time, 1),
    )


@router.get("/ping")
async def ping():
    """Simple liveness probe."""
    return {"status": "ok"}


@router.get("/healthz")
async def healthz():
    """Deep liveness for external monitoring (Uptime Kuma).

    Returns 200 only if the process is up AND Postgres answers a trivial
    query. Unlike /ping (process-only) and /health (always 200, folds in
    NHS/Ollama), this fails fast with 503 when the DB is unreachable — which
    is exactly the 'container running but API broken' case we want to catch.
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"healthz DB check failed: {e}")
        return JSONResponse(status_code=503, content={"status": "db_error"})
    return {"status": "ok"}
