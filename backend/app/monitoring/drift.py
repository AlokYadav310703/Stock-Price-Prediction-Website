"""
Data drift monitoring — Population Stability Index (PSI) and the
Kolmogorov–Smirnov statistic, computed from real stored feature snapshots
(app.models.feature_snapshot.FeatureSnapshot). No numbers here are
hardcoded: with too little history, a feature is reported as
"insufficient data" rather than assigned a fabricated status.
"""
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.feature_snapshot import FeatureSnapshot

FEATURES = ["rsi", "macd", "volume", "atr", "momentum", "sentiment_score"]
FEATURE_LABELS = {"rsi": "RSI", "macd": "MACD", "volume": "Volume", "atr": "ATR", "momentum": "Momentum", "sentiment_score": "Sentiment Score"}

MIN_REFERENCE_ROWS = 30
MIN_COMPARISON_ROWS = 10


def _psi(reference: np.ndarray, comparison: np.ndarray, bins: int = 10) -> Optional[float]:
    if len(reference) < 5 or len(comparison) < 5:
        return None
    edges = np.quantile(reference, np.linspace(0, 1, bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    edges = np.unique(edges)
    if len(edges) < 3:
        return None

    ref_counts, _ = np.histogram(reference, bins=edges)
    cmp_counts, _ = np.histogram(comparison, bins=edges)

    ref_pct = np.clip(ref_counts / max(len(reference), 1), 1e-4, None)
    cmp_pct = np.clip(cmp_counts / max(len(comparison), 1), 1e-4, None)

    return float(np.sum((cmp_pct - ref_pct) * np.log(cmp_pct / ref_pct)))


def _ks_statistic(reference: np.ndarray, comparison: np.ndarray) -> Optional[float]:
    if len(reference) < 5 or len(comparison) < 5:
        return None
    try:
        from scipy import stats

        return float(stats.ks_2samp(reference, comparison).statistic)
    except ImportError:
        # Lightweight fallback without scipy: max distance between empirical CDFs.
        all_vals = np.sort(np.concatenate([reference, comparison]))
        ref_sorted, cmp_sorted = np.sort(reference), np.sort(comparison)
        ref_cdf = np.searchsorted(ref_sorted, all_vals, side="right") / len(ref_sorted)
        cmp_cdf = np.searchsorted(cmp_sorted, all_vals, side="right") / len(cmp_sorted)
        return float(np.max(np.abs(ref_cdf - cmp_cdf)))


def _status(psi: Optional[float], settings) -> str:
    if psi is None:
        return "insufficient_data"
    if psi >= settings.DRIFT_PSI_HIGH_THRESHOLD:
        return "high_drift"
    if psi >= settings.DRIFT_PSI_WARNING_THRESHOLD:
        return "warning"
    return "normal"


def compute_drift_report(db: Session, reference_days: int = 60, comparison_days: int = 30) -> dict:
    settings = get_settings()

    rows = (
        db.query(FeatureSnapshot)
        .order_by(FeatureSnapshot.date.asc())
        .all()
    )

    if len(rows) < MIN_REFERENCE_ROWS + MIN_COMPARISON_ROWS:
        return {
            "reference_window": "Insufficient history",
            "comparison_window": "Insufficient history",
            "features": [
                {"feature": FEATURE_LABELS[f], "psi": 0.0, "ks": 0.0, "status": "insufficient_data"} for f in FEATURES
            ],
            "thresholds": {"warning": settings.DRIFT_PSI_WARNING_THRESHOLD, "high_drift": settings.DRIFT_PSI_HIGH_THRESHOLD},
        }

    comparison_rows = rows[-comparison_days:]
    reference_rows = rows[: max(len(rows) - comparison_days, MIN_REFERENCE_ROWS)]

    features_out = []
    for f in FEATURES:
        ref_vals = np.array([getattr(r, f) for r in reference_rows if getattr(r, f) is not None], dtype=float)
        cmp_vals = np.array([getattr(r, f) for r in comparison_rows if getattr(r, f) is not None], dtype=float)
        psi = _psi(ref_vals, cmp_vals)
        ks = _ks_statistic(ref_vals, cmp_vals)
        features_out.append(
            {
                "feature": FEATURE_LABELS[f],
                "psi": round(psi, 4) if psi is not None else 0.0,
                "ks": round(ks, 4) if ks is not None else 0.0,
                "status": _status(psi, settings),
            }
        )

    return {
        "reference_window": f"{reference_rows[0].date} – {reference_rows[-1].date}",
        "comparison_window": f"{comparison_rows[0].date} – {comparison_rows[-1].date}",
        "features": features_out,
        "thresholds": {"warning": settings.DRIFT_PSI_WARNING_THRESHOLD, "high_drift": settings.DRIFT_PSI_HIGH_THRESHOLD},
    }
