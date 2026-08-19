"""
One row per trading day of the raw feature values used by the model
(technical indicators + news sentiment). This is the source of truth for
drift monitoring: recent rows are compared statistically (PSI / KS) against
an older reference window, so drift is always computed from real logged
values rather than hardcoded.
"""
from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class FeatureSnapshot(Base):
    __tablename__ = "feature_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False, default="AAPL", index=True)
    date = Column(String, nullable=False, unique=True, index=True)  # YYYY-MM-DD, one row per trading day

    rsi = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    atr = Column(Float, nullable=True)
    momentum = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
