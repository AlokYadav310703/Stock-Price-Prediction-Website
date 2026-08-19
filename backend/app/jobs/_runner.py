"""
Shared helper: wraps a job's execution with a JobRun row (RUNNING ->
SUCCESS/FAILED) so the /monitoring/health endpoint can report whether the
latest scheduled job succeeded, and dispatches a CRITICAL alert on failure.
"""
import logging
import sys
import traceback
from contextlib import contextmanager
from datetime import datetime

from app.config import get_settings
from app.database import SessionLocal
from app.models.job_run import JobRun

# Standalone job scripts (python -m app.jobs.X) never import app.main, so
# logging.basicConfig() would otherwise never run and every logger.info/
# error() call below would be silently dropped. Configure it here,
# idempotently, so `python -m app.jobs.X` always produces visible output
# both locally and in CI.
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=get_settings().LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )

logger = logging.getLogger("app.jobs")

_db_initialized = False


def _ensure_db_initialized():
    """Standalone job scripts never import app.main, so the FastAPI startup
    event that normally calls init_db() never runs. Call it here instead,
    once per process, so a fresh database (e.g. a newly created Postgres
    instance with no tables yet) gets its schema created automatically
    before any job tries to write to it."""
    global _db_initialized
    if not _db_initialized:
        from app.database import init_db

        init_db()
        _db_initialized = True


@contextmanager
def job_run(job_name: str):
    _ensure_db_initialized()
    logger.info("Starting job '%s'...", job_name)

    # Setup (creating the JobRun row itself) can fail — most commonly a bad
    # or unreachable DATABASE_URL. That must NOT fail silently: log it with
    # a full traceback before re-raising, since this happens before the
    # try/except below even exists.
    try:
        db = SessionLocal()
        run = JobRun(job_name=job_name, status="RUNNING")
        db.add(run)
        db.commit()
        db.refresh(run)
    except Exception:
        logger.error(
            "Job '%s' failed during setup (could not create JobRun row — check "
            "DATABASE_URL is correct and reachable):\n%s",
            job_name,
            traceback.format_exc(),
        )
        raise

    result = {"records_processed": 0}
    try:
        yield db, result
        run.status = "SUCCESS"
        run.records_processed = result.get("records_processed", 0)
        logger.info("Job '%s' succeeded (%s records).", job_name, run.records_processed)
    except Exception as exc:
        run.status = "FAILED"
        run.error_message = str(exc)
        logger.error("Job '%s' failed: %s\n%s", job_name, exc, traceback.format_exc())
        try:
            from app.monitoring.alerting import check_job_failure

            check_job_failure(db, job_name, str(exc))
        except Exception:
            logger.error("Additionally failed to record the job-failure alert.")
        raise
    finally:
        run.finished_at = datetime.utcnow()
        db.commit()
        db.close()