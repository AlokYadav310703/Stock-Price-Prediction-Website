from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml.exceptions import MarketDataError, ModelNotAvailableError, PredictionError
from app.schemas.prediction import LatestPredictionOut
from app.services.prediction_service import generate_prediction

router = APIRouter(tags=["prediction"])


@router.post("/predict", response_model=LatestPredictionOut)
def trigger_prediction(db: Session = Depends(get_db)):
    """Manually trigger a full prediction run.

    The daily scheduled job (app/jobs/daily_prediction.py) is the primary
    path in production — this exists for manual/testing use and so the
    frontend can offer an explicit "run now" action if desired.
    """
    try:
        row = generate_prediction(db)
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ModelNotAvailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PredictionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return LatestPredictionOut(**{c.name: getattr(row, c.name) for c in row.__table__.columns}, previous_prediction=None)
