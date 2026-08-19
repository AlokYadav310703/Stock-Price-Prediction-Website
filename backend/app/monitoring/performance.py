"""
Performance metrics — computed live from the Prediction table, never
hardcoded (spec section 27/9). Directional correctness itself is decided
once, at update-time, in app/services/actual_price_service.py using a
configurable rule; this module only aggregates what's already stored.
"""
import math
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.prediction import Prediction

RANGE_DAYS = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}


def _range_cutoff(range_key: str) -> Optional[str]:
    if range_key == "all":
        return None
    days = RANGE_DAYS.get(range_key, 90)
    return (date.today() - timedelta(days=days)).isoformat()


def get_predictions_in_range(db: Session, symbol: str, range_key: str):
    q = db.query(Prediction).filter(Prediction.symbol == symbol)
    cutoff = _range_cutoff(range_key)
    if cutoff:
        q = q.filter(Prediction.prediction_date >= cutoff)
    return q.order_by(Prediction.prediction_date.asc()).all()


def compute_performance_metrics(db: Session, symbol: str, range_key: str = "90d") -> dict:
    rows = [r for r in get_predictions_in_range(db, symbol, range_key) if r.actual_price is not None]

    if not rows:
        return {"insufficient_data": True}

    n = len(rows)
    mae = sum(r.absolute_error for r in rows) / n
    rmse = math.sqrt(sum((r.error or 0) ** 2 for r in rows) / n)
    mape = sum(r.percentage_error for r in rows) / n
    correct = sum(1 for r in rows if r.is_correct)
    incorrect = n - correct

    mean_actual = sum(r.actual_price for r in rows) / n
    ss_res = sum((r.actual_price - r.predicted_price) ** 2 for r in rows)
    ss_tot = sum((r.actual_price - mean_actual) ** 2 for r in rows)
    r2 = (1 - ss_res / ss_tot) if ss_tot > 0 else None

    return {
        "insufficient_data": False,
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "mape": round(mape, 3),
        "r2": round(r2, 3) if r2 is not None else None,
        "directional_accuracy": round((correct / n) * 100, 1),
        "correct": correct,
        "incorrect": incorrect,
        "total": n,
    }


def compute_performance_trend(db: Session, symbol: str, chunk_size: int = 5) -> list:
    rows = [r for r in get_predictions_in_range(db, symbol, "all") if r.actual_price is not None]
    trend = []
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i : i + chunk_size]
        if not chunk:
            continue
        n = len(chunk)
        mae = sum(r.absolute_error for r in chunk) / n
        rmse = math.sqrt(sum((r.error or 0) ** 2 for r in chunk) / n)
        acc = (sum(1 for r in chunk if r.is_correct) / n) * 100
        trend.append(
            {
                "date": chunk[-1].prediction_date,
                "mae": round(mae, 2),
                "rmse": round(rmse, 2),
                "directional_accuracy": round(acc, 1),
            }
        )
    return trend


def compute_prediction_distribution(db: Session, symbol: str, lookback: int = 60) -> dict:
    rows = db.query(Prediction).filter(Prediction.symbol == symbol).order_by(Prediction.prediction_date.desc()).limit(lookback).all()
    changes = [round(r.predicted_price - r.base_price, 2) for r in rows]
    counts = {"UP": 0, "DOWN": 0, "FLAT": 0}
    for r in rows:
        counts[r.predicted_direction] = counts.get(r.predicted_direction, 0) + 1
    return {"predicted_changes": changes, "direction_counts": counts}
