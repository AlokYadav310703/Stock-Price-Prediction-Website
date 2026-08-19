"""
Automatic actual-price matching (spec section 28).

For every prediction whose target_date has passed and whose actual_price is
still NULL, fetch that day's close and back-fill: actual_price,
actual_direction, is_correct, error, absolute_error, percentage_error.

Directional correctness rule (kept in one place, configurable):
predicted direction is measured as predicted_price vs. base_price (the
close at prediction time); actual direction is measured as actual_price vs.
the same base_price. This mirrors the Streamlit app's own reasoning and
matches spec section 8.
"""
import logging
from datetime import date

from sqlalchemy.orm import Session

from app.ml import feature_engineering as fe
from app.ml.exceptions import MarketDataError
from app.models.prediction import Prediction

logger = logging.getLogger("app.services.actual_price_service")


def _direction(new_price: float, base_price: float) -> str:
    if new_price > base_price:
        return "UP"
    if new_price < base_price:
        return "DOWN"
    return "FLAT"


def update_pending_actual_prices(db: Session, symbol: str) -> int:
    """Back-fill actual prices for predictions whose target_date has passed.

    Returns the number of rows updated. Raises MarketDataError if the price
    feed itself can't be reached at all (caller/job decides how to log that).
    """
    today = date.today().isoformat()
    pending = (
        db.query(Prediction)
        .filter(Prediction.symbol == symbol, Prediction.actual_price.is_(None), Prediction.target_date <= today)
        .all()
    )
    if not pending:
        return 0

    df = fe.fetch_ohlc(symbol, lookback=len(pending) + 10)
    # Build a date -> close lookup from the fetched window.
    df = df.copy()
    df["date_str"] = df["date"].dt.date.astype(str)
    close_by_date = dict(zip(df["date_str"], df["close"]))

    updated = 0
    for pred in pending:
        actual = close_by_date.get(pred.target_date)
        if actual is None or (isinstance(actual, float) and actual != actual):  # NaN check
            continue  # not available yet (e.g. today hasn't closed)

        actual = float(actual)
        pred.actual_price = round(actual, 2)
        pred.actual_direction = _direction(actual, pred.base_price)
        pred.is_correct = pred.predicted_direction == pred.actual_direction
        pred.error = round(pred.predicted_price - actual, 2)
        pred.absolute_error = round(abs(pred.error), 2)
        pred.percentage_error = round((pred.absolute_error / actual) * 100, 2) if actual else None
        updated += 1

    db.commit()
    logger.info("Matched actual prices for %d prediction(s).", updated)
    return updated
