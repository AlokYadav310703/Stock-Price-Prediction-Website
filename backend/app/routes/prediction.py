from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.ml.exceptions import MarketDataError, ModelNotAvailableError, PredictionError
from app.ml.news_service import fetch_news_articles  # Add this import
from app.models.prediction import Prediction
from app.schemas.prediction import (
    BasePredictions,
    LatestPredictionOut,
    MarketReturns,
    NewsFeatures,
    PredictionDetailOut,
)

router = APIRouter(prefix="/prediction", tags=["prediction"])


def _latest_two(db: Session):
    settings = get_settings()
    rows = (
        db.query(Prediction)
        .filter(Prediction.symbol == settings.STOCK_SYMBOL)
        .order_by(Prediction.prediction_date.desc())
        .limit(2)
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail="No predictions available yet. Run the daily prediction job first.")
    return rows


@router.get("/latest", response_model=LatestPredictionOut)
def get_latest_prediction(db: Session = Depends(get_db)):
    rows = _latest_two(db)
    latest = rows[0]
    previous_prediction = rows[1].predicted_price if len(rows) > 1 else None
    return LatestPredictionOut(**{c.name: getattr(latest, c.name) for c in latest.__table__.columns}, previous_prediction=previous_prediction)


def _format_news_articles_for_display(articles: list) -> list:
    """Convert fetched news articles to similar_events format for UI display."""
    similar_events = []
    
    for article in articles[:3]:  # Top 3 articles
        similar_events.append({
            "title": article.get("title", "Unknown Title")[:100],  # Truncate for display
            "date": article.get("published_at", "n/a"),
            "source": article.get("source", "Unknown Source"),
            "url": article.get("url", ""),
            "similarity": 1.0,  # These are actual news, not similar matches
            "direction": "NEUTRAL",  # Default direction for fetched news
        })
    
    return similar_events


@router.get("/latest/detail", response_model=PredictionDetailOut)
def get_latest_prediction_detail(db: Session = Depends(get_db)):
    latest = _latest_two(db)[0]

    expected_move_pct = ((latest.predicted_price - latest.base_price) / latest.base_price) * 100 if latest.base_price else 0.0
    if expected_move_pct > 2:
        recommendation = "STRONG BUY"
    elif expected_move_pct > 0.5:
        recommendation = "BUY"
    elif expected_move_pct < -2:
        recommendation = "STRONG SELL"
    elif expected_move_pct < -0.5:
        recommendation = "SELL"
    else:
        recommendation = "HOLD"

    # ✅ FETCH NEWS ARTICLES AND FORMAT THEM
    articles = fetch_news_articles(num_articles=3)
    similar_events = _format_news_articles_for_display(articles)

    return PredictionDetailOut(
        prediction_date=latest.prediction_date,
        target_date=latest.target_date,
        model_version=latest.model_version,
        current_price=latest.base_price,
        stage1_prediction=latest.stage1_prediction,
        base_predictions=BasePredictions(lstm=latest.lstm_prediction, cnn=latest.cnn_prediction),
        final_prediction=latest.predicted_price,
        correction=latest.correction,
        news_features=NewsFeatures(
            sentiment_score=latest.sentiment_score,
            impact_score=latest.impact_score,
            event_weight=latest.event_weight,
            news_count=latest.news_count,
            has_supply_chain_event=int(latest.has_supply_chain_event) if latest.has_supply_chain_event is not None else None,
        ),
        market_returns=MarketReturns(return_1d=latest.return_1d, return_5d=latest.return_5d),
        expected_move_pct=round(expected_move_pct, 2),
        recommendation=recommendation,
        similar_events=similar_events,  # ✅ NOW POPULATED WITH FETCHED NEWS
    )
