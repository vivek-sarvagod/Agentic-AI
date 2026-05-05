"""
config.py
----------
Central settings loaded from environment variables or a .env file.
Pydantic-settings validates types automatically — if OPENAI_API_KEY
is missing it becomes None (not a crash), enabling demo mode.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Environment ───────────────────────────────────────────────
    AGENT_ENV: str = "development"

    # ── OpenAI (optional — system works without it in demo mode) ──
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # ── Service URLs ──────────────────────────────────────────────
    # Must point to your running portal-survey-api instance
    API_BASE_URL: str = "http://localhost:8000"
    MCP_SERVER_URL: str = "http://localhost:8002/sse"

    # ── MCP vs REST API ───────────────────────────────────────────
    # Set to True to use MCP server (requires SSE transport)
    # Set to False to use REST API (default, recommended)
    USE_MCP_TOOLS: bool = False

    # ── CORS ──────────────────────────────────────────────────────
    # In development: "*"
    # In production: "https://your-frontend-domain.com"
    ALLOWED_ORIGINS: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()

# """
# config.py
# ----------
# Central settings loaded from environment variables or a .env file.
# Pydantic-settings validates types automatically — if OPENAI_API_KEY
# is missing it becomes None (not a crash), enabling demo mode.
# """
# from pydantic_settings import BaseSettings, SettingsConfigDict


# class Settings(BaseSettings):
#     # ── Environment ───────────────────────────────────────────────
#     AGENT_ENV: str = "development"

#     # ── OpenAI (optional — system works without it in demo mode) ──
#     OPENAI_API_KEY: str | None = None
#     OPENAI_MODEL: str = "gpt-4o-mini"

#     # ── Service URLs ──────────────────────────────────────────────
#     # Must point to your running portal-survey-api instance
#     API_BASE_URL: str = "http://localhost:8000"
#     MCP_SERVER_URL: str = "http://localhost:8000/mcp"

#     # ── CORS ──────────────────────────────────────────────────────
#     # In development: "*"
#     # In production: "https://your-frontend-domain.com"
#     ALLOWED_ORIGINS: str = "*"

#     model_config = SettingsConfigDict(
#         env_file=".env",
#         env_file_encoding="utf-8",
#         case_sensitive=True,
#     )


# settings = Settings()