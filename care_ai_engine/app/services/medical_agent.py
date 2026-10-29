"""
Care AI Engine - Medical Agent v2 (MCP-Powered)
Uses MCP to fetch LIVE NHS data instead of pre-scraped ChromaDB.

Flow:
  1. User asks a question
  2. MCP client fetches live data from NHS.uk
  3. LLM generates answer grounded in the live NHS data
  4. Response includes source URLs for verification

No scraping. No stale data. Always current.
"""

import time
from typing import Optional

from app.core.logging import get_logger
from app.mcp.client.mcp_client import mcp_client
from app.services.llm_service import llm_service, LLMError

logger = get_logger("medical_agent")

# System prompt optimised for small LLMs (3b-8b)
# Short, explicit rules. Small models ignore long instructions.
SYSTEM_PROMPT = """You are a UK care assistant AI. You answer medical questions using NHS data.

RULES:
1. ONLY use the NHS data provided below. Do NOT make up information.
2. If the data does not answer the question, say: "I could not find this in NHS data."
3. Be concise. Use plain English. Use UK spelling.
4. NEVER diagnose or prescribe. Say "consult your doctor" for specific decisions.
5. Format medication dosages exactly as shown in the NHS data.
6. For emergencies, say: Call 999 or NHS 111."""


def _assess_confidence(context: str, sources: list) -> str:
    """Assess confidence based on whether good NHS data was found."""
    if not context or not context.strip():
        return "low"
    if len(sources) >= 2 and len(context) > 500:
        return "high"
    if len(sources) >= 1 and len(context) > 200:
        return "medium"
    return "low"


def _format_context_for_prompt(context: str, sources: list) -> str:
    """Format the MCP-fetched context into a structured prompt block."""
    if not context:
        return "No NHS data available for this query."

    source_header = "\n".join(
        f"[Source: {s.get('source', 'NHS')} — {s.get('name', '')}] ({s.get('url', '')})"
        for s in sources
    )

    return f"""--- NHS LIVE DATA ---
{source_header}

{context}
--- END NHS DATA ---"""


async def ask_medical_agent(
        question: str,
        strategy: str = "auto",
        include_sources: bool = True,
        **kwargs,
) -> dict:
    """
    Main MCP-powered RAG pipeline:
      1. FETCH: MCP client gets live NHS data
      2. AUGMENT: Build prompt with the fetched context
      3. GENERATE: LLM answers using the live data

    Args:
        question: The user's medical question
        strategy: "auto", "medicine", "condition", or "search"
        include_sources: Whether to include source URLs in response

    Returns:
        dict with answer, sources, confidence, model_used, processing_time_ms
    """
    start = time.monotonic()

    # 1. FETCH: Get live NHS data via MCP
    mcp_result = await mcp_client.fetch_medical_context(
        question=question,
        strategy=strategy,
    )

    context = mcp_result["context"]
    sources = mcp_result["sources"]
    tools_used = mcp_result["tools_used"]

    confidence = _assess_confidence(context, sources)

    logger.info(
        "MCP data fetched",
        extra={
            "query": question[:100],
            "tools_used": tools_used,
            "sources_found": len(sources),
            "context_length": len(context),
        },
    )

    # 2. AUGMENT: Build the prompt with live NHS data
    formatted_context = _format_context_for_prompt(context, sources)

    user_prompt = f"""{formatted_context}

QUESTION: {question}

Answer using ONLY the NHS data above. Be concise and accurate."""

    # 3. GENERATE: Get LLM response
    try:
        llm_result = await llm_service.generate(
            prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.2,  # Low temperature for medical accuracy
        )
    except LLMError as e:
        logger.error(f"LLM failed for question: {question[:100]}", exc_info=True)
        raise

    # 4. Build response
    processing_time_ms = (time.monotonic() - start) * 1000

    response_sources = []
    if include_sources:
        for src in sources:
            response_sources.append({
                "source": src.get("source", "NHS"),
                "name": src.get("name", ""),
                "url": src.get("url", ""),
                "type": "live",  # Indicates this was fetched live, not from cache
            })

    logger.info(
        "Medical query answered",
        extra={
            "query": question[:100],
            "confidence": confidence,
            "tools_used": tools_used,
            "sources_count": len(sources),
            "duration_ms": round(processing_time_ms, 1),
        },
    )

    return {
        "answer": llm_result["response"],
        "sources": response_sources,
        "confidence": confidence,
        "model_used": llm_result["model"],
        "processing_time_ms": round(processing_time_ms, 1),
        "tokens_used": llm_result.get("tokens_used", 0),
        "tools_used": tools_used,
        "data_freshness": "live",
    }
