from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.monitoring.performance import compute_performance_metrics, compute_performance_trend
from app.schemas.monitoring import PerformanceMetricsOut, PerformanceTrendPoint

router = APIRouter(tags=["performance"])


@router.get("/performance", response_model=PerformanceMetricsOut)
def get_performance(range: str = Query("90d", description="7d | 30d | 90d | 1y | all"), db: Session = Depends(get_db)):
    settings = get_settings()
    return compute_performance_metrics(db, settings.STOCK_SYMBOL, range)


@router.get("/performance/trend", response_model=list[PerformanceTrendPoint])
def get_performance_trend(db: Session = Depends(get_db)):
    settings = get_settings()
    return compute_performance_trend(db, settings.STOCK_SYMBOL)
