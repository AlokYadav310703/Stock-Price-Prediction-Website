from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(prefix="/model", tags=["model"])


@router.get("/about")
def get_about_model():
    settings = get_settings()
    return {
        "name": f"{settings.STOCK_SYMBOL} Next-Day Price Predictor",
        "version": settings.MODEL_VERSION,
        "architecture": [
            {
                "stage": "Stage 1 — Ensemble",
                "detail": (
                    "LSTM and CNN base learners trained on 30-day OHLC windows, combined by a "
                    "meta-learner into a single next-day price estimate."
                ),
            },
            {
                "stage": "Stage 2 — News-aware correction",
                "detail": (
                    "A gradient-boosted regressor adjusts the Stage 1 estimate using same-day news "
                    "sentiment, impact and event-weight features retrieved via similarity search, "
                    "plus 1-day and 5-day market returns."
                ),
            },
        ],
        "features": [
            "Open / High / Low / Close (30-day window)",
            "1-day and 5-day price returns",
            "News sentiment score (vector-similarity weighted)",
            "News impact score",
            "Event weight (e.g. supply-chain events)",
        ],
        "training_period": "See MODEL_VERSION / model card shipped alongside the model files.",
        "prediction_methodology": (
            "A scheduled job runs once per trading day after market close, fetches the latest OHLC "
            "data, computes technical indicators and news features, runs the two-stage model, and "
            "stores the prediction. Actual prices are matched automatically the following trading day."
        ),
        "limitations": [
            "Directional accuracy, not price-level accuracy, is the primary success metric.",
            "News coverage gaps fall back to neutral sentiment features.",
            "The model can drift during regime changes if not periodically retrained.",
            "Not intended as financial advice; outputs are informational only.",
        ],
    }
