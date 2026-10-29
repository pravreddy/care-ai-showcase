"""
Care AI Engine - Configuration
All settings loaded from environment variables. Nothing hardcoded.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from .env file or environment variables."""

    # --- Application ---
    app_name: str = "CareAI Engine"
    app_env: str = "production"
    app_debug: bool = False
    app_port: int = 8000
    app_host: str = "0.0.0.0"
    app_version: str = "1.0.0"
    secret_key: str = "change-me"
    allowed_origins: str = "http://localhost:3000"

    # --- OAuth / Social Login ---
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: Optional[str] = None
    
    # microsoft_client_id: Optional[str] = None
    # microsoft_client_secret: Optional[str] = None
    # microsoft_tenant_id: str = "common"  # Use 'common' for any Microsoft account
    # microsoft_redirect_uri: Optional[str] = None

    # --- LLM Provider ---
    # Set to "groq" for cloud (fast, free tier) or "ollama" for self-hosted (private)
    llm_provider: str = "groq"

    # --- LLM: Ollama (self-hosted) ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_timeout: int = 120
    ollama_max_tokens: int = 2048

    # --- LLM: Groq (cloud — free tier, no credit card needed) ---
    # Get your key at: https://console.groq.com/keys
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"
    # Other good Groq models:
    #   "llama-3.1-8b-instant"         — fastest, highest free tier limits (14,400 req/day)
    #   "llama-3.3-70b-versatile"      — best quality, good for care/clinical (6,000 TPM free)
    #   "deepseek-r1-distill-llama-70b" — strong reasoning

    # --- MCP (Model Context Protocol) ---
    mcp_nhs_enabled: bool = True
    mcp_nhs_request_timeout: int = 15
    mcp_nhs_cache_ttl: int = 300  # Cache NHS pages for 5 min (reduces load on NHS)

    # --- Database (PostgreSQL) ---
    database_url: str = "postgresql+asyncpg://careai:careai_secret@localhost:5432/careai"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600

    # --- Authentication ---
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # --- Rate Limiting ---
    rate_limit_free_queries_per_day: int = 50
    rate_limit_free_voice_notes_per_day: int = 10
    rate_limit_pro_queries_per_day: int = 0  # 0 = unlimited
    rate_limit_pro_voice_notes_per_day: int = 0

    # --- Storage (ZDR: Zero Data Retention for media) ---
    # No upload_dir needed — media is processed in memory and destroyed.
    # Only text transcripts and clinical notes are stored in PostgreSQL.
    max_audio_upload_mb: int = 100   # Max audio file size accepted
    max_video_upload_mb: int = 500   # Max video file size accepted

    # --- Whisper ---
    whisper_model_size: str = "base"
    whisper_language: str = "en"

    # --- NHS Data ---
    nhs_scrape_interval_hours: int = 168
    nhs_user_agent: str = "CareAI-Engine/1.0"

    # --- Logging ---
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = "./logs/careai.log"

    # --- Metrics ---
    enable_metrics: bool = True
    metrics_port: int = 9090

    # --- Stripe ---
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_price_pro: Optional[str] = None
    stripe_price_agency: Optional[str] = None

    # --- Admin ---
    admin_emails: str = ""  # Comma-separated emails that get is_admin=True on register

    @property
    def admin_email_list(self) -> list[str]:
        if not self.admin_emails:
            return []
        return [e.strip().lower() for e in self.admin_emails.split(",")]

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"
    
    @property
    def google_oauth_enabled(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)
    
    # @property
    # def microsoft_oauth_enabled(self) -> bool:
    #     return bool(self.microsoft_client_id and self.microsoft_client_secret)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    """Singleton settings instance, cached after first load."""
    return Settings()
