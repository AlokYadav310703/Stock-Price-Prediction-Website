class MarketDataError(Exception):
    """Raised when OHLC data can't be fetched or is invalid (NaNs, empty, too short)."""


class ModelNotAvailableError(Exception):
    """Raised when required model/scaler files are missing from MODEL_DIR."""


class PredictionError(Exception):
    """Raised when the prediction pipeline itself fails after models loaded fine."""
