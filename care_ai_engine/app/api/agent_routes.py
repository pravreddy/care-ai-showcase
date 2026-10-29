"""
Care AI Engine - Medical Agent API Routes v2
MCP-powered: queries fetch live NHS data, no pre-scraped database needed.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

from app.services.medical_agent import ask_medical_agent
from app.services.llm_service import LLMError
from app.mcp.client.mcp_client import mcp_client
from app.services import cache_service
from app.middleware.auth import get_current_user
from app.models.database import User
from app.core.logging import get_logger

logger = get_logger("api.agent")

router = APIRouter(prefix="/agent", tags=["Medical Agent"])


# --- Request/Response models ---

class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    include_sources: bool = True
    strategy: str = Field(
        default="auto",
        description="Data strategy: 'auto', 'medicine', 'condition', or 'search'",
    )


class AskResponse(BaseModel):
    answer: str
    sources: list[dict] = []
    confidence: Optional[str] = None
    model_used: str
    processing_time_ms: float
    tools_used: list[str] = []
    data_freshness: str = "live"
    disclaimer: str = (
        "This information is based on NHS and UK medical sources. "
        "Always consult a qualified healthcare professional for medical advice."
    )


class MCPToolRequest(BaseModel):
    """Direct MCP tool call — for advanced users and API integrations."""
    tool_name: str
    arguments: dict = {}


class MCPToolResponse(BaseModel):
    success: bool
    data: dict
    tool: str
    duration_ms: float


# --- Endpoints ---

@router.post("/ask", response_model=AskResponse)
async def ask_question(
    req: AskRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Ask the medical AI agent a question.
    
    Fetches LIVE NHS data via MCP, then generates an answer using the local LLM.
    Data is always current — no stale cache.
    """
    try:
        result = await ask_medical_agent(
            question=req.question,
            strategy=req.strategy,
            include_sources=req.include_sources,
        )

        return AskResponse(
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"],
            model_used=result["model_used"],
            processing_time_ms=result["processing_time_ms"],
            tools_used=result.get("tools_used", []),
            data_freshness=result.get("data_freshness", "live"),
        )

    except LLMError as e:
        logger.error(f"LLM error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI engine is temporarily unavailable. Please try again shortly.",
        )
    except Exception as e:
        logger.error(f"Unexpected error in ask endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.post("/mcp/call", response_model=MCPToolResponse)
async def call_mcp_tool(
    req: MCPToolRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Directly call an MCP tool without LLM processing.
    
    Useful for:
    - Fetching raw NHS data for display in your app
    - Building custom UIs that show medicine/condition info
    - API integrations that don't need AI summarisation
    """
    result = await mcp_client.call_tool(req.tool_name, req.arguments)

    return MCPToolResponse(
        success=result.get("success", False),
        data=result,
        tool=req.tool_name,
        duration_ms=result.get("_meta", {}).get("duration_ms", 0),
    )


@router.get("/mcp/tools")
async def list_mcp_tools(
    current_user: User = Depends(get_current_user),
):
    """List all available MCP tools and their descriptions."""
    return {
        "tools": mcp_client.available_tools,
        "count": len(mcp_client.available_tools),
    }


@router.get("/cache/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_user),
):
    """
    View cache statistics: hit rate, cached entries, Redis status.
    High hit rate = most queries are fast (from cache).
    """
    stats = await cache_service.get_cache_stats()
    return stats


@router.post("/cache/flush")
async def flush_cache(
    tool_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """
    Flush the cache. Use when NHS updates data and you want fresh results.
    
    - No tool_name: flushes everything
    - With tool_name: flushes only that tool's cache
    """
    if tool_name:
        count = await cache_service.invalidate_all_for_tool(tool_name)
        return {"flushed": count, "tool": tool_name}
    else:
        # Flush all MCP caches
        total = 0
        for tool in mcp_client.available_tools:
            total += await cache_service.invalidate_all_for_tool(tool["name"])
        return {"flushed": total, "tool": "all"}
