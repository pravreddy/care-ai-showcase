"""
Care AI Engine - Trial (Try AI) Routes
Allows visitors to test the AI without logging in.
Rate-limited by IP address using Redis.
"""

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from typing import Optional

from app.services.medical_agent import ask_medical_agent
from app.services.llm_service import LLMError
from app.services import cache_service
from app.core.config import get_settings
from app.core.logging import get_logger

import hashlib
import time

logger = get_logger("api.trial")

router = APIRouter(prefix="/trial", tags=["Trial"])

# --- Config ---
TRIAL_MAX_QUERIES = 5
TRIAL_WINDOW_SECONDS = 86400  # 24 hours
TRIAL_MAX_QUESTION_LENGTH = 500  # Shorter than logged-in users


# --- Models ---

class TrialAskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=TRIAL_MAX_QUESTION_LENGTH)


class TrialAskResponse(BaseModel):
    answer: str
    sources: list[dict] = []
    confidence: Optional[str] = None
    model_used: str
    processing_time_ms: float
    tools_used: list[str] = []
    data_freshness: str = "live"
    queries_remaining: int
    disclaimer: str = (
        "This information is based on NHS and UK medical sources. "
        "Always consult a qualified healthcare professional for medical advice."
    )


class TrialStatusResponse(BaseModel):
    queries_used: int
    queries_remaining: int
    resets_in_seconds: int


# --- Helpers ---

def _get_client_ip(request: Request) -> str:
    """Get real client IP, accounting for reverse proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # First IP in the chain is the real client
        return forwarded.split(",")[0].strip()
    return request.client.host


def _get_trial_key(ip: str) -> str:
    """Hash IP for privacy — we don't store raw IPs."""
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
    return f"trial:ratelimit:{ip_hash}"


async def _check_trial_limit(request: Request) -> tuple[int, int, int]:
    """
    Check and increment trial usage.
    Returns (queries_used, queries_remaining, ttl_seconds).
    Raises 429 if limit exceeded.
    """
    ip = _get_client_ip(request)
    key = _get_trial_key(ip)

    try:
        redis = await cache_service.get_redis()
    except Exception:
        logger.warning("Redis unavailable for trial rate limiting — allowing request")
        return (0, TRIAL_MAX_QUERIES, TRIAL_WINDOW_SECONDS)

    try:
        # Get current count
        count = await redis.get(key)

        if count is not None and int(count) >= TRIAL_MAX_QUERIES:
            ttl = await redis.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": "You've used all your free trial queries. Sign up for unlimited access!",
                    "queries_used": TRIAL_MAX_QUERIES,
                    "queries_remaining": 0,
                    "resets_in_seconds": max(ttl, 0),
                    "signup_url": "/register",
                },
            )

        # Increment counter
        pipe = redis.pipeline()
        pipe.incr(key)
        if count is None:
            # First query — set expiry
            pipe.expire(key, TRIAL_WINDOW_SECONDS)
        results = await pipe.execute()

        new_count = results[0]
        ttl = await redis.ttl(key)

        return (new_count, TRIAL_MAX_QUERIES - new_count, max(ttl, 0))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Redis error in trial rate limit: {e}")
        return (0, TRIAL_MAX_QUERIES, TRIAL_WINDOW_SECONDS)


# --- Endpoints ---

@router.get("/status", response_model=TrialStatusResponse)
async def trial_status(request: Request):
    """
    Check how many trial queries remain for this visitor.
    No auth required.
    """
    ip = _get_client_ip(request)
    key = _get_trial_key(ip)

    try:
        redis = await cache_service.get_redis()
    except Exception:
        return TrialStatusResponse(
            queries_used=0,
            queries_remaining=TRIAL_MAX_QUERIES,
            resets_in_seconds=TRIAL_WINDOW_SECONDS,
        )

    try:
        count = await redis.get(key)
        ttl = await redis.ttl(key) if count else TRIAL_WINDOW_SECONDS

        used = int(count) if count else 0
        return TrialStatusResponse(
            queries_used=used,
            queries_remaining=max(TRIAL_MAX_QUERIES - used, 0),
            resets_in_seconds=max(ttl, 0),
        )
    except Exception as e:
        logger.error(f"Redis error in trial status: {e}")
        return TrialStatusResponse(
            queries_used=0,
            queries_remaining=TRIAL_MAX_QUERIES,
            resets_in_seconds=TRIAL_WINDOW_SECONDS,
        )


@router.post("/ask", response_model=TrialAskResponse)
async def trial_ask(req: TrialAskRequest, request: Request):
    """
    Ask the AI a medical question — no login required.
    Limited to 5 queries per 24 hours per IP address.
    """
    # Check rate limit
    queries_used, queries_remaining, ttl = await _check_trial_limit(request)

    logger.info(
        f"Trial query from {_get_client_ip(request)[:8]}***: "
        f"'{req.question[:50]}...' (used: {queries_used}/{TRIAL_MAX_QUERIES})"
    )

    try:
        result = await ask_medical_agent(
            question=req.question,
            strategy="auto",
            include_sources=True,
        )

        return TrialAskResponse(
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"],
            model_used=result["model_used"],
            processing_time_ms=result["processing_time_ms"],
            tools_used=result.get("tools_used", []),
            data_freshness=result.get("data_freshness", "live"),
            queries_remaining=queries_remaining,
        )

    except LLMError as e:
        logger.error(f"LLM error in trial: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI engine is temporarily unavailable. Please try again shortly.",
        )
    except Exception as e:
        logger.error(f"Unexpected error in trial ask: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )
