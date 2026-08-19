"""
Daily prediction job.

Run with:
    python -m app.jobs.daily_prediction

Fetches the latest market data, engineers features, runs the two-stage
model, and stores exactly one new Prediction row. Designed to run once per
trading day via GitHub Actions (see .github/workflows/daily-prediction.yml)
or any external cron service — NOT via an in-process scheduler inside the
FastAPI server, which free-tier hosts can't be relied on to keep alive.
"""
import logging
import sys
import traceback

from app.config import get_settings
from app.jobs._runner import job_run
from app.services.prediction_service import generate_prediction

logger = logging.getLogger("app.jobs.daily_prediction")


def main() -> int:
    logger.info("Starting daily prediction job for %s", get_settings().STOCK_SYMBOL)
    try:
        with job_run("daily_prediction") as (db, result):
            row = generate_prediction(db)
            result["records_processed"] = 1
            logger.info(
                "Prediction stored: %s -> %s, predicted=%.2f, direction=%s",
                row.prediction_date,
                row.target_date,
                row.predicted_price,
                row.predicted_direction,
            )
        return 0
    except Exception:
        logger.error("daily_prediction job aborted:\n%s", traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
