"""
Care AI Engine - Main Application v2 (MCP Architecture)
FastAPI app with MCP-powered medical agent. No scraping or pre-loading needed.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger, new_correlation_id
from app.core.database import init_db, close_db
from app.mcp.client.mcp_client import mcp_client
from app.services.cache_service import close_redis
from app.services.oauth_service import init_oauth
from app.api import (
    auth_routes, oauth_routes, agent_routes, health_routes,
    notes_routes, partner_routes, coupon_routes, trial_routes,
)

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # --- STARTUP ---
    setup_logging()
    settings = get_settings()

    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Architecture: MCP (live NHS data)")

    # Initialise database (users, subscriptions, usage)
    await init_db()

    # Initialise OAuth providers
    init_oauth()
    if settings.google_oauth_enabled:
        logger.info("OAuth: Google login enabled")
    else:
        logger.info("OAuth: Google login not configured (set GOOGLE_CLIENT_ID & GOOGLE_CLIENT_SECRET)")

    # MCP client is ready immediately — no data to pre-load!
    tools = mcp_client.available_tools
    logger.info(f"MCP tools available: {len(tools)}")
    for t in tools:
        logger.info(f"  → {t['name']} ({t['server']})")

    logger.info("All services initialised. Ready to serve requests.")

    yield

    # --- SHUTDOWN ---
    logger.info("Shutting down...")
    await close_redis()
    await close_db()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "AI-powered medical knowledge engine for UK care workers. "
            "Uses MCP (Model Context Protocol) to fetch live NHS data "
            "and a local LLM for private, UK-based AI processing."
        ),
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # --- Session middleware (required for OAuth state) ---
    # Must be added BEFORE CORS middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie="careai_session",
        max_age=600,  # 10 min — only needed during OAuth flow
        same_site="lax",
        https_only=settings.is_production,
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Request middleware ---
    @app.middleware("http")
    async def add_correlation_id(request: Request, call_next):
        """Add correlation ID to every request for tracing."""
        cid = new_correlation_id()
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response

    # --- Global exception handler ---
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal error occurred. Please try again later.",
                "support": "If this persists, contact support@yourdomain.co.uk",
            },
        )

    # --- Register Routes ---
    app.include_router(health_routes.router)
    app.include_router(auth_routes.router, prefix="/api/v1")
    app.include_router(oauth_routes.router, prefix="/api/v1")
    app.include_router(agent_routes.router, prefix="/api/v1")
    app.include_router(notes_routes.router, prefix="/api/v1")
    app.include_router(partner_routes.router, prefix="/api/v1")
    app.include_router(coupon_routes.router, prefix="/api/v1")
    app.include_router(trial_routes.router, prefix="/api/v1")

    return app


# Create the app instance
app = create_app()
