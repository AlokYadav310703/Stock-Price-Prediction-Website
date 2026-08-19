from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class JobRun(Base):
    __tablename__ = "job_runs"

    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String, nullable=False, index=True)  # daily_prediction | update_actual_prices | monitoring
    status = Column(String, nullable=False)                # RUNNING | SUCCESS | FAILED
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String, nullable=True)
    records_processed = Column(Integer, nullable=True)
