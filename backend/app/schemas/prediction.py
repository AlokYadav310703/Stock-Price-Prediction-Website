from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    prediction_date: str
    target_date: str
    base_price: float
    predicted_price: float
    actual_price: Optional[float] = None
    predicted_direction: str
    actual_direction: Optional[str] = None
    is_correct: Optional[bool] = None
    error: Optional[float] = None
    absolute_error: Optional[float] = None
    percentage_error: Optional[float] = None
    model_version: str
    created_at: datetime


class LatestPredictionOut(PredictionOut):
    previous_prediction: Optional[float] = None


class BasePredictions(BaseModel):
    lstm: Optional[float] = None
    cnn: Optional[float] = None


class NewsFeatures(BaseModel):
    sentiment_score: Optional[float] = None
    impact_score: Optional[float] = None
    event_weight: Optional[float] = None
    news_count: Optional[int] = None
    has_supply_chain_event: Optional[int] = None


class MarketReturns(BaseModel):
    return_1d: Optional[float] = None
    return_5d: Optional[float] = None


class SimilarEvent(BaseModel):
    title: str
    date: str
    similarity: float
    direction: str


class PredictionDetailOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    prediction_date: str
    target_date: str
    model_version: str
    current_price: float
    stage1_prediction: Optional[float] = None
    base_predictions: BasePredictions
    final_prediction: float
    correction: Optional[float] = None
    news_features: NewsFeatures
    market_returns: MarketReturns
    expected_move_pct: float
    recommendation: str
    similar_events: list[SimilarEvent] = []


class StockSummaryOut(BaseModel):
    symbol: str
    name: str
    current_price: float
    previous_close: float
    change: float
    change_pct: float
    as_of: str
