"""
Prediction orchestration service.

This is the single place that runs the full pipeline (fetch data -> feature
engineering -> Stage 1 -> Stage 2 -> persist). Both the POST /api/predict
endpoint and app/jobs/daily_prediction.py call into this module so there is
exactly one implementation of "how a prediction gets made."
"""
import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.config import get_settings
from app.ml import feature_engineering as fe
from app.ml import model_service
from app.ml import news_service
from app.ml.exceptions import MarketDataError, ModelNotAvailableError, PredictionError
from app.models.feature_snapshot import FeatureSnapshot
from app.models.prediction import Prediction

logger = logging.getLogger("app.services.prediction_service")


def _next_trading_day(d: date) -> date:
    nxt = d + timedelta(days=1)
    while nxt.weekday() >= 5:  # Sat/Sun
        nxt += timedelta(days=1)
    return nxt


def _direction(new_price: float, base_price: float) -> str:
    if new_price > base_price:
        return "UP"
    if new_price < base_price:
        return "DOWN"
    return "FLAT"


def generate_prediction(db: Session) -> Prediction:
    """Run the full pipeline once and store a new Prediction row.

    Raises MarketDataError / ModelNotAvailableError / PredictionError on
    failure — callers (route or job) decide how to surface that.
    """
    settings = get_settings()
    symbol = settings.STOCK_SYMBOL

    df = fe.fetch_ohlc(symbol, lookback=30)
    current_price = float(df.iloc[-1]["close"])
    prediction_date = df.iloc[-1]["date"].date() if hasattr(df.iloc[-1]["date"], "date") else date.today()
    target_date = _next_trading_day(prediction_date)

    market_returns = fe.compute_market_returns(df)
    indicators = fe.compute_technical_indicators(df)

    # Store today's feature snapshot for drift monitoring regardless of
    # whether the model itself is available yet.
    _upsert_feature_snapshot(db, symbol, prediction_date.isoformat(), indicators, news_sentiment=None)

    models = model_service.load_models()  # raises ModelNotAvailableError if missing
    try:
        stage1_price, base_preds = model_service.run_stage1(models, df)
        news_features, _similar_events = news_service.get_aggregated_news_features()
        final_price, correction = model_service.run_stage2(models, stage1_price, news_features, market_returns)
    except Exception as exc:
        if isinstance(exc, PredictionError):
            raise
        raise PredictionError(f"Prediction pipeline failed: {exc}") from exc

    # Update the feature snapshot with the actual sentiment score used.
    _upsert_feature_snapshot(
        db, symbol, prediction_date.isoformat(), indicators, news_sentiment=news_features.get("sentiment_score")
    )

    row = Prediction(
        symbol=symbol,
        prediction_date=prediction_date.isoformat(),
        target_date=target_date.isoformat(),
        base_price=current_price,
        predicted_price=round(final_price, 2),
        predicted_direction=_direction(final_price, current_price),
        stage1_prediction=round(stage1_price, 2),
        lstm_prediction=round(base_preds["lstm"], 2),
        cnn_prediction=round(base_preds["cnn"], 2),
        correction=round(correction, 2),
        sentiment_score=news_features.get("sentiment_score"),
        impact_score=news_features.get("impact_score"),
        event_weight=news_features.get("event_weight"),
        news_count=news_features.get("news_count"),
        has_supply_chain_event=bool(news_features.get("has_supply_chain_event")),
        return_1d=market_returns.get("return_1d"),
        return_5d=market_returns.get("return_5d"),
        model_version=model_service.get_model_version(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info("Stored prediction %s -> %s (%.2f)", row.prediction_date, row.target_date, row.predicted_price)
    return row


def _upsert_feature_snapshot(db: Session, symbol: str, date_str: str, indicators: dict, news_sentiment):
    existing = db.query(FeatureSnapshot).filter(FeatureSnapshot.symbol == symbol, FeatureSnapshot.date == date_str).first()
    if existing:
        existing.rsi = indicators.get("rsi")
        existing.macd = indicators.get("macd")
        existing.atr = indicators.get("atr")
        existing.momentum = indicators.get("momentum")
        existing.volume = indicators.get("volume")
        if news_sentiment is not None:
            existing.sentiment_score = news_sentiment
    else:
        db.add(
            FeatureSnapshot(
                symbol=symbol,
                date=date_str,
                rsi=indicators.get("rsi"),
                macd=indicators.get("macd"),
                atr=indicators.get("atr"),
                momentum=indicators.get("momentum"),
                volume=indicators.get("volume"),
                sentiment_score=news_sentiment,
            )
        )
    db.commit()
