from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String, nullable=False, index=True)  # PERFORMANCE | DRIFT | DATA_QUALITY | JOB
    severity = Column(String, nullable=False, index=True)    # INFO | WARNING | CRITICAL
    message = Column(String, nullable=False)
    resolved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
