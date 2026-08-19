"""
Shared helper: wraps a job's execution with a JobRun row (RUNNING ->
SUCCESS/FAILED) so the /monitoring/health endpoint can report whether the
latest scheduled job succeeded, and dispatches a CRITICAL alert on failure.
"""
import logging
import traceback
from contextlib import contextmanager

from app.database import SessionLocal
from app.models.job_run import JobRun
from app.monitoring.alerting import check_job_failure

logger = logging.getLogger("app.jobs")


@contextmanager
def job_run(job_name: str):
    db = SessionLocal()
    run = JobRun(job_name=job_name, status="RUNNING")
    db.add(run)
    db.commit()
    db.refresh(run)

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
            check_job_failure(db, job_name, str(exc))
        except Exception:
            logger.error("Additionally failed to record the job-failure alert.")
        raise
    finally:
        from datetime import datetime

        run.finished_at = datetime.utcnow()
        db.commit()
        db.close()
