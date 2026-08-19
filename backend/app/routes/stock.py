from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.prediction import Prediction
from app.schemas.prediction import StockSummaryOut

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("/summary", response_model=StockSummaryOut)
def get_stock_summary(db: Session = Depends(get_db)):
    settings = get_settings()
    rows = (
        db.query(Prediction)
        .filter(Prediction.symbol == settings.STOCK_SYMBOL)
        .order_by(Prediction.prediction_date.desc())
        .limit(2)
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail="No prediction data available yet. Run the daily prediction job first.")

    latest = rows[0]
    previous_close = rows[1].base_price if len(rows) > 1 else latest.base_price
    change = round(latest.base_price - previous_close, 2)
    change_pct = round((change / previous_close) * 100, 2) if previous_close else 0.0

    return StockSummaryOut(
        symbol=settings.STOCK_SYMBOL,
        name=settings.STOCK_NAME,
        current_price=latest.base_price,
        previous_close=previous_close,
        change=change,
        change_pct=change_pct,
        as_of=latest.prediction_date,
    )
