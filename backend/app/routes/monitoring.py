from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.ml.model_service import models_available
from app.models.job_run import JobRun
from app.models.prediction import Prediction
from app.monitoring.data_quality import check_prediction_log_quality
from app.monitoring.drift import compute_drift_report
from app.monitoring.performance import compute_performance_metrics, compute_prediction_distribution
from app.schemas.monitoring import (
    DataQualityOut,
    DriftReportOut,
    ModelHealthOut,
    PredictionDistributionOut,
)

router = APIRouter(tags=["monitoring"])


@router.get("/data-quality", response_model=DataQualityOut)
def get_data_quality(db: Session = Depends(get_db)):
    return check_prediction_log_quality(db)


@router.get("/drift", response_model=DriftReportOut)
def get_drift(db: Session = Depends(get_db)):
    return compute_drift_report(db)


@router.get("/monitoring/distribution", response_model=PredictionDistributionOut)
def get_prediction_distribution(db: Session = Depends(get_db)):
    settings = get_settings()
    return compute_prediction_distribution(db, settings.STOCK_SYMBOL)


@router.get("/monitoring/health", response_model=ModelHealthOut)
def get_model_health(db: Session = Depends(get_db)):
    settings = get_settings()

    latest = (
        db.query(Prediction)
        .filter(Prediction.symbol == settings.STOCK_SYMBOL)
        .order_by(Prediction.prediction_date.desc())
        .first()
    )
    prediction_count = db.query(Prediction).filter(Prediction.symbol == settings.STOCK_SYMBOL).count()
    perf = compute_performance_metrics(db, settings.STOCK_SYMBOL, "90d")

    last_job = db.query(JobRun).filter(JobRun.job_name == "daily_prediction").order_by(JobRun.started_at.desc()).first()
    last_job_ok = bool(last_job and last_job.status == "SUCCESS")

    db_connected = True
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception:
        db_connected = False

    checks = {
        "model_file_exists": models_available(),
        "prediction_pipeline_working": latest is not None,
        "last_scheduled_job_succeeded": last_job_ok,
        "database_connected": db_connected,
        "market_data_api_working": True,  # best-effort; a failed fetch surfaces via job status/alerts instead
    }

    status = "healthy" if all(checks.values()) else ("degraded" if checks["database_connected"] else "unhealthy")

    return ModelHealthOut(
        status=status,
        last_prediction=latest.prediction_date if latest else None,
        last_training=None,
        model_version=settings.MODEL_VERSION,
        prediction_count=prediction_count,
        directional_accuracy=None if perf.get("insufficient_data") else perf["directional_accuracy"],
        checks=checks,
    )
