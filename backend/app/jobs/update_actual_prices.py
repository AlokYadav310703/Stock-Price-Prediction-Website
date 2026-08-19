"""
Actual-price matching job.

Run with:
    python -m app.jobs.update_actual_prices

For every prediction whose target_date has passed and actual_price is still
NULL, fetches the real close price and back-fills error/direction/
correctness fields. Intended to run once per trading day, shortly after
daily_prediction.py (see .github/workflows/daily-prediction.yml, which
chains both).
"""
import logging
import sys
import traceback

from app.config import get_settings
from app.jobs._runner import job_run
from app.services.actual_price_service import update_pending_actual_prices

logger = logging.getLogger("app.jobs.update_actual_prices")


def main() -> int:
    settings = get_settings()
    logger.info("Starting actual-price update job for %s", settings.STOCK_SYMBOL)
    try:
        with job_run("update_actual_prices") as (db, result):
            updated = update_pending_actual_prices(db, settings.STOCK_SYMBOL)
            result["records_processed"] = updated
            logger.info("Updated %d prediction(s) with actual prices.", updated)
        return 0
    except Exception:
        logger.error("update_actual_prices job aborted:\n%s", traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
