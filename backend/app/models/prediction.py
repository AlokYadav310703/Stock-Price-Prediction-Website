"""
Prediction table.

One row per prediction ever generated. Rows are NEVER overwritten — when
the actual price becomes available, the same row is updated in place with
actual_price / error fields (see app/jobs/update_actual_prices.py), but a
new prediction always creates a new row so historical performance can be
analyzed in full.
"""
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)

    # ── Identity ────────────────────────────────────────────────────────
    symbol = Column(String, nullable=False, default="AAPL", index=True)
    prediction_date = Column(String, nullable=False, index=True)  # date the prediction was made (YYYY-MM-DD)
    target_date = Column(String, nullable=False, index=True)      # date being predicted (YYYY-MM-DD)

    # ── Prices ──────────────────────────────────────────────────────────
    base_price = Column(Float, nullable=False)        # close price at prediction time
    predicted_price = Column(Float, nullable=False)   # final (Stage 2) predicted price
    actual_price = Column(Float, nullable=True)        # NULL until target_date's close is known

    # ── Direction & correctness (recomputed once actual_price lands) ────
    predicted_direction = Column(String, nullable=False)   # UP | DOWN | FLAT
    actual_direction = Column(String, nullable=True)
    is_correct = Column(Boolean, nullable=True)

    # ── Error metrics (derived, but persisted for fast historical reads) ─
    error = Column(Float, nullable=True)
    absolute_error = Column(Float, nullable=True)
    percentage_error = Column(Float, nullable=True)

    # ── Two-stage pipeline detail (reproducibility, section 24) ─────────
    stage1_prediction = Column(Float, nullable=True)
    lstm_prediction = Column(Float, nullable=True)
    cnn_prediction = Column(Float, nullable=True)
    correction = Column(Float, nullable=True)

    # ── News / market features used for this prediction ─────────────────
    sentiment_score = Column(Float, nullable=True)
    impact_score = Column(Float, nullable=True)
    event_weight = Column(Float, nullable=True)
    news_count = Column(Integer, nullable=True)
    has_supply_chain_event = Column(Boolean, nullable=True)
    return_1d = Column(Float, nullable=True)
    return_5d = Column(Float, nullable=True)

    # ── Reproducibility ───────────────────────────────────────────────
    model_version = Column(String, nullable=False)
    feature_version = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
