from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.prediction import Prediction
from app.monitoring.performance import get_predictions_in_range
from app.schemas.prediction import PredictionOut

router = APIRouter(tags=["predictions"])


@router.get("/predictions", response_model=list[PredictionOut])
def list_predictions(
    limit: int = Query(30, ge=1, le=100000),
    range: Optional[str] = Query(None, description="7d | 30d | 90d | 1y | all"),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    if range:
        rows = get_predictions_in_range(db, settings.STOCK_SYMBOL, range)
        rows = rows[-limit:]
        return list(reversed(rows))

    rows = (
        db.query(Prediction)
        .filter(Prediction.symbol == settings.STOCK_SYMBOL)
        .order_by(Prediction.prediction_date.desc())
        .limit(limit)
        .all()
    )
    return rows


@router.get("/predictions/{target_date}", response_model=PredictionOut)
def get_prediction_by_date(target_date: str, db: Session = Depends(get_db)):
    settings = get_settings()
    row = (
        db.query(Prediction)
        .filter(Prediction.symbol == settings.STOCK_SYMBOL, Prediction.prediction_date == target_date)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"No prediction found for {target_date}.")
    return row
