"""
Application configuration.

Everything that can vary between local dev, CI, and production is read from
environment variables here — nothing below should ever be hardcoded in
route/service code. See .env.example for the full list with comments.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── App ────────────────────────────────────────────────────────────
    APP_NAME: str = "AAPL Prediction & Monitoring API"
    ENVIRONMENT: str = "development"  # development | production
    LOG_LEVEL: str = "INFO"

    # ── Database ───────────────────────────────────────────────────────
    # Production: a managed Postgres URL, e.g.
    #   postgresql+psycopg2://user:pass@host:5432/dbname
    # Local dev without Docker/Postgres: sqlite works out of the box.
    DATABASE_URL: str = "sqlite:///./aapl_predictor.db"

    # ── CORS ───────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ── Stock / data source ───────────────────────────────────────────
    STOCK_SYMBOL: str = "AAPL"
    STOCK_NAME: str = "Apple Inc."
    NEWS_API_KEY: str = "1671260b3d8341d59df512e6cd64224f"

    # ── ChromaDB / HuggingFace (news similarity) ──────────────────────
    HF_REPO_ID: str = "alokyadav310703/Similarity"
    HF_COLLECTION_NAME: str = "aapl_memory_v2"
    CHROMA_CACHE_DIR: str = "./.cache/chroma"

    # ── Models ─────────────────────────────────────────────────────────
    MODEL_DIR: str = "../models"
    MODEL_VERSION: str = "v2.3.1"
    CORRECTION_MODEL_FILENAME: str = "Best_Adjustment_Model.pkl"

    # ── Directional-correctness rule (kept configurable per spec) ──────
    # "previous_close": predicted/actual direction measured against the
    # prior trading day's close (the Streamlit app's own convention).
    DIRECTION_RULE: str = "previous_close"

    # ── Monitoring thresholds ───────────────────────────────────────────
    DIRECTIONAL_ACCURACY_WARNING_THRESHOLD: float = 55.0
    DRIFT_PSI_WARNING_THRESHOLD: float = 0.15
    DRIFT_PSI_HIGH_THRESHOLD: float = 0.25
    DATA_QUALITY_VOLUME_SPIKE_PCT: float = 15.0

    # ── Alerting (future channels; DB+dashboard only for now) ──────────
    ALERT_EMAIL_ENABLED: bool = False
    ALERT_DISCORD_WEBHOOK_URL: str = ""
    ALERT_SLACK_WEBHOOK_URL: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
