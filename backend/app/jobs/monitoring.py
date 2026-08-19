"""
Monitoring job.

Run with:
    python -m app.jobs.monitoring

Runs data-quality checks, drift checks, and performance-threshold checks,
generating Alert rows whenever a threshold is exceeded. Intended to run
once per trading day after daily_prediction.py and update_actual_prices.py.
"""
import logging
import sys
import traceback

from app.config import get_settings
from app.jobs._runner import job_run
from app.ml import feature_engineering as fe
from app.monitoring.alerting import check_data_quality, check_directional_accuracy, check_drift
from app.monitoring.data_quality import check_ohlc_quality, check_prediction_log_quality
from app.monitoring.drift import compute_drift_report
from app.monitoring.performance import compute_performance_metrics

logger = logging.getLogger("app.jobs.monitoring")


def main() -> int:
    settings = get_settings()
    logger.info("Starting monitoring job for %s", settings.STOCK_SYMBOL)
    try:
        with job_run("monitoring") as (db, result):
            checks_run = 0

            quality = check_prediction_log_quality(db)
            try:
                df = fe.fetch_ohlc(settings.STOCK_SYMBOL, lookback=30)
                quality["checks"].extend(check_ohlc_quality(df))
            except Exception as exc:
                logger.warning("Could not fetch OHLC for data-quality checks: %s", exc)
            check_data_quality(db, quality)
            checks_run += 1

            drift_report = compute_drift_report(db)
            check_drift(db, drift_report)
            checks_run += 1

            performance = compute_performance_metrics(db, settings.STOCK_SYMBOL, "90d")
            check_directional_accuracy(db, performance)
            checks_run += 1

            result["records_processed"] = checks_run
            logger.info("Monitoring job completed: %d check group(s) run.", checks_run)
        return 0
    except Exception:
        logger.error("monitoring job aborted:\n%s", traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
