from typing import Optional

from pydantic import BaseModel


class PerformanceMetricsOut(BaseModel):
    insufficient_data: bool
    mae: Optional[float] = None
    rmse: Optional[float] = None
    mape: Optional[float] = None
    r2: Optional[float] = None
    directional_accuracy: Optional[float] = None
    correct: Optional[int] = None
    incorrect: Optional[int] = None
    total: Optional[int] = None


class PerformanceTrendPoint(BaseModel):
    date: str
    mae: float
    rmse: float
    directional_accuracy: float


class DataQualityCheck(BaseModel):
    name: str
    status: str  # ok | warning
    detail: str


class DataQualityOut(BaseModel):
    records_last_24h: int
    total_records: int
    missing_values: int
    duplicate_records: int
    invalid_values: int
    checks: list[DataQualityCheck]


class DriftFeature(BaseModel):
    feature: str
    psi: float
    ks: float
    status: str  # normal | warning | high_drift


class DriftThresholds(BaseModel):
    warning: float
    high_drift: float


class DriftReportOut(BaseModel):
    reference_window: str
    comparison_window: str
    features: list[DriftFeature]
    thresholds: DriftThresholds


class DirectionCounts(BaseModel):
    UP: int
    DOWN: int
    FLAT: int


class PredictionDistributionOut(BaseModel):
    predicted_changes: list[float]
    direction_counts: DirectionCounts


class HealthChecks(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_file_exists: bool
    prediction_pipeline_working: bool
    last_scheduled_job_succeeded: bool
    database_connected: bool
    market_data_api_working: bool


class ModelHealthOut(BaseModel):
    model_config = {"protected_namespaces": ()}

    status: str  # healthy | degraded | unhealthy
    last_prediction: Optional[str] = None
    last_training: Optional[str] = None
    model_version: str
    prediction_count: int
    directional_accuracy: Optional[float] = None
    checks: HealthChecks
