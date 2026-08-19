"""
Alerting.

For now, alerts are created in the database and rendered on the /alerts
page. `dispatch_alert` is the single choke point where a real integration
(email / Discord / Slack) would be added later — swap or extend it without
touching the threshold-checking logic below.
"""
import logging

import requests
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.alert import Alert

logger = logging.getLogger("app.monitoring.alerting")


def dispatch_alert(db: Session, alert_type: str, severity: str, message: str) -> Alert:
    """Persist an alert and fan it out to any configured external channel."""
    alert = Alert(alert_type=alert_type, severity=severity, message=message, resolved=False)
    db.add(alert)
    db.commit()
    db.refresh(alert)

    settings = get_settings()
    if settings.ALERT_DISCORD_WEBHOOK_URL:
        _send_webhook(settings.ALERT_DISCORD_WEBHOOK_URL, f"**[{severity}] {alert_type}**\n{message}")
    if settings.ALERT_SLACK_WEBHOOK_URL:
        _send_webhook(settings.ALERT_SLACK_WEBHOOK_URL, f"*[{severity}] {alert_type}*\n{message}")
    # ALERT_EMAIL_ENABLED would plug into an SMTP/provider call here.

    return alert


def _send_webhook(url: str, text: str):
    try:
        requests.post(url, json={"content": text, "text": text}, timeout=10)
    except Exception as exc:
        logger.error("Failed to deliver alert webhook: %s", exc)


def check_directional_accuracy(db: Session, performance: dict) -> None:
    settings = get_settings()
    if performance.get("insufficient_data"):
        return
    acc = performance["directional_accuracy"]
    if acc < settings.DIRECTIONAL_ACCURACY_WARNING_THRESHOLD:
        dispatch_alert(
            db,
            alert_type="PERFORMANCE",
            severity="WARNING",
            message=(
                f"Directional accuracy dropped to {acc}%, below the "
                f"{settings.DIRECTIONAL_ACCURACY_WARNING_THRESHOLD}% threshold."
            ),
        )


def check_drift(db: Session, drift_report: dict) -> None:
    for feature in drift_report["features"]:
        if feature["status"] == "high_drift":
            dispatch_alert(
                db,
                alert_type="DRIFT",
                severity="WARNING",
                message=(
                    f"Feature '{feature['feature']}' shows high drift (PSI {feature['psi']}, "
                    f"threshold {drift_report['thresholds']['high_drift']}) vs. the reference window."
                ),
            )


def check_data_quality(db: Session, quality_report: dict) -> None:
    for check in quality_report["checks"]:
        if check["status"] == "warning":
            dispatch_alert(db, alert_type="DATA_QUALITY", severity="INFO", message=check["detail"])


def check_job_failure(db: Session, job_name: str, error_message: str) -> None:
    dispatch_alert(
        db,
        alert_type="JOB",
        severity="CRITICAL",
        message=f"Scheduled job '{job_name}' failed: {error_message}",
    )
