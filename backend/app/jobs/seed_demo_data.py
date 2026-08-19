"""
Seed the database with a realistic prediction history for local testing and
demos — useful before real trained model files are available, or when you
just want to see every endpoint/page working end-to-end.

This is NOT part of the production pipeline. It exists only so
`uvicorn app.main:app` + this script gives you a fully working API on day
one. Delete the rows (or drop the DB) before going to production.

Run with:
    python -m app.jobs.seed_demo_data
"""
import random
import sys
from datetime import date, timedelta

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.models.alert import Alert
from app.models.feature_snapshot import FeatureSnapshot
from app.models.prediction import Prediction


def _is_trading_day(d: date) -> bool:
    return d.weekday() < 5


def _direction(new_price: float, base_price: float) -> str:
    if new_price > base_price:
        return "UP"
    if new_price < base_price:
        return "DOWN"
    return "FLAT"


def main():
    init_db()
    settings = get_settings()
    symbol = settings.STOCK_SYMBOL
    rng = random.Random(20260817)

    db = SessionLocal()
    existing = db.query(Prediction).filter(Prediction.symbol == symbol).count()
    if existing > 0:
        print(f"{existing} predictions already exist for {symbol} — skipping seed. "
              f"Delete the DB file / table to reseed.")
        db.close()
        return 0

    today = date.today()
    days = []
    cursor = today - timedelta(days=210)
    while cursor <= today:
        if _is_trading_day(cursor):
            days.append(cursor)
        cursor += timedelta(days=1)

    price = 227.5
    for i, d in enumerate(days):
        target = d + timedelta(days=1)
        while target.weekday() >= 5:
            target += timedelta(days=1)

        drift = 0.35 * ((i % 36) / 18 - 1)
        noise = (rng.random() - 0.5) * 4.2
        next_actual = max(140.0, price + drift + noise) if i < len(days) - 1 else None

        model_noise = (rng.random() - 0.5) * 3.4
        model_bias = (rng.random() - 0.48) * 1.6
        predicted_price = price + drift + model_bias + model_noise
        predicted_direction = _direction(predicted_price, price)

        is_pending = i >= len(days) - 3
        actual_price = actual_direction = is_correct = error = abs_error = pct_error = None
        if not is_pending and next_actual is not None:
            actual_price = round(next_actual, 2)
            actual_direction = _direction(actual_price, price)
            is_correct = predicted_direction == actual_direction
            error = round(predicted_price - actual_price, 2)
            abs_error = round(abs(error), 2)
            pct_error = round((abs_error / actual_price) * 100, 2)

        stage1 = predicted_price + (rng.random() - 0.5) * 1.2
        db.add(
            Prediction(
                symbol=symbol,
                prediction_date=d.isoformat(),
                target_date=target.isoformat(),
                base_price=round(price, 2),
                predicted_price=round(predicted_price, 2),
                actual_price=actual_price,
                predicted_direction=predicted_direction,
                actual_direction=actual_direction,
                is_correct=is_correct,
                error=error,
                absolute_error=abs_error,
                percentage_error=pct_error,
                stage1_prediction=round(stage1, 2),
                lstm_prediction=round(stage1 + (rng.random() - 0.5) * 0.8, 2),
                cnn_prediction=round(stage1 + (rng.random() - 0.5) * 0.8, 2),
                correction=round(predicted_price - stage1, 2),
                sentiment_score=round(rng.random() * 2 - 1, 2),
                impact_score=round(rng.random(), 2),
                event_weight=round(rng.random(), 2),
                news_count=3,
                has_supply_chain_event=rng.random() > 0.85,
                return_1d=round((rng.random() - 0.5) * 2, 2),
                return_5d=round((rng.random() - 0.5) * 4, 2),
                model_version=settings.MODEL_VERSION,
            )
        )

        db.add(
            FeatureSnapshot(
                symbol=symbol,
                date=d.isoformat(),
                rsi=round(30 + rng.random() * 40, 2),
                macd=round((rng.random() - 0.5) * 2, 3),
                volume=round(40_000_000 + rng.random() * 30_000_000, 0),
                atr=round(1.5 + rng.random() * 2, 2),
                momentum=round((rng.random() - 0.5) * 6, 2),
                sentiment_score=round(rng.random() * 2 - 1, 2),
            )
        )

        if next_actual is not None:
            price = next_actual

    db.add(
        Alert(
            alert_type="PERFORMANCE",
            severity="INFO",
            message="Demo data seeded — this alert confirms the alerting pipeline renders correctly.",
            resolved=True,
        )
    )

    db.commit()
    count = db.query(Prediction).filter(Prediction.symbol == symbol).count()
    print(f"Seeded {count} predictions for {symbol}.")
    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
