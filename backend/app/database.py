"""
SQLAlchemy engine/session setup.

Works against SQLite (local dev, no Docker needed) or PostgreSQL
(production) purely based on DATABASE_URL — no code branching needed.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables if they don't exist.

    For a real production rollout, replace with Alembic migrations — this
    is intentionally kept simple for the MVP so `uvicorn app.main:app`
    works with zero extra setup against a fresh database.
    """
    from app.models import prediction, alert, feature_snapshot, job_run  # noqa: F401

    Base.metadata.create_all(bind=engine)
