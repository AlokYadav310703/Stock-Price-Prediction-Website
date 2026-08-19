"""
Two-stage model loading and inference.

Ported from the Streamlit app: Stage 1 is an LSTM+CNN ensemble (combined by
a meta-learner) predicting next-day price from a 30-day OHLC window; Stage 2
is a sklearn regressor that corrects the Stage 1 estimate using same-day
news + market-return features.

TensorFlow/joblib are imported lazily so the rest of the API (health,
history, alerts, etc.) works even in environments where the heavier ML
dependencies or the model files themselves aren't present yet — a very
real situation for a free-tier deployment mid-build. Callers get a clear
ModelNotAvailableError instead of an import crash at process startup.
"""
import logging
from pathlib import Path

import numpy as np

from app.config import get_settings
from app.ml.exceptions import ModelNotAvailableError, PredictionError
from app.ml.news_service import STAGE2_FEATURE_ORDER

logger = logging.getLogger("app.ml.model_service")

_models_cache = {}

REQUIRED_FILES = [
    "lstm_model.keras",
    "cnn_model.keras",
    "feature_scaler.pkl",
    "target_scaler.pkl",
    "feature_scaler_raw.pkl",
    "target_scaler_raw.pkl",
]


def model_dir() -> Path:
    return Path(get_settings().MODEL_DIR).resolve()


def models_available() -> bool:
    """Cheap existence check used by the health endpoint — no heavy imports."""
    d = model_dir()
    correction_file = get_settings().CORRECTION_MODEL_FILENAME
    meta_ok = (d / "meta_model.pkl").exists() or (d / "meta_learner.pkl").exists()
    return d.exists() and meta_ok and (d / correction_file).exists() and all((d / f).exists() for f in REQUIRED_FILES)


def load_models() -> dict:
    """Load all trained models + scalers, caching them in-process.

    Raises ModelNotAvailableError with a specific missing-file message if
    anything required is absent — callers (routes, jobs) turn that into a
    clean 503 / job-failure rather than a stack trace.
    """
    if _models_cache:
        return _models_cache

    d = model_dir()
    settings = get_settings()

    if not d.exists():
        raise ModelNotAvailableError(f"Model directory not found: {d}")

    try:
        import joblib
        import tensorflow as tf
    except ImportError as exc:
        raise ModelNotAvailableError(
            "tensorflow/joblib are not installed. Install backend/requirements.txt "
            "in full to run real predictions."
        ) from exc

    missing = [f for f in REQUIRED_FILES if not (d / f).exists()]
    if missing:
        raise ModelNotAvailableError(f"Missing required model files in {d}: {missing}")

    correction_path = d / settings.CORRECTION_MODEL_FILENAME
    if not correction_path.exists():
        raise ModelNotAvailableError(f"Correction model not found: {correction_path}")

    models = {}
    models["lstm"] = tf.keras.models.load_model(str(d / "lstm_model.keras"))
    models["cnn"] = tf.keras.models.load_model(str(d / "cnn_model.keras"))

    meta_path = d / "meta_model.pkl"
    if not meta_path.exists():
        meta_path = d / "meta_learner.pkl"
    if not meta_path.exists():
        raise ModelNotAvailableError(f"Meta-learner not found in {d} (expected meta_model.pkl or meta_learner.pkl).")
    models["meta_learner"] = joblib.load(meta_path)

    models["correction_model"] = joblib.load(correction_path)
    for f in REQUIRED_FILES[2:]:
        models[f.replace(".pkl", "")] = joblib.load(d / f)

    _models_cache.update(models)
    logger.info("Models loaded from %s", d)
    return models


def get_model_version() -> str:
    return get_settings().MODEL_VERSION


def prepare_ohlc_window(df, scaler, lookback: int) -> np.ndarray:
    ohlc = df[["open", "high", "low", "close"]].values.astype(float)
    if np.isnan(ohlc).any():
        raise PredictionError("NaN values found in OHLC data — cannot prepare model input.")
    if len(ohlc) < lookback:
        ohlc = np.vstack([np.zeros((lookback - len(ohlc), 4)), ohlc])
    else:
        ohlc = ohlc[-lookback:]
    scaled = scaler.transform(ohlc)
    return scaled.reshape(1, lookback, 4)


def run_stage1(models: dict, df) -> tuple[float, dict]:
    lookback = models["lstm"].input_shape[1]
    ohlc_lstm = prepare_ohlc_window(df, models["feature_scaler_raw"], lookback)
    ohlc_cnn = prepare_ohlc_window(df, models["feature_scaler"], lookback)

    lstm_scaled = models["lstm"].predict(ohlc_lstm, verbose=0)
    cnn_scaled = models["cnn"].predict(ohlc_cnn, verbose=0)
    meta_input = np.hstack([lstm_scaled, cnn_scaled])
    stage1_scaled = np.array(models["meta_learner"].predict(meta_input)).reshape(-1, 1)

    lstm_actual = float(models["target_scaler_raw"].inverse_transform(lstm_scaled)[0, 0])
    cnn_actual = float(models["target_scaler"].inverse_transform(cnn_scaled)[0, 0])
    stage1_actual = float(models["target_scaler"].inverse_transform(stage1_scaled)[0, 0])

    return stage1_actual, {"lstm": lstm_actual, "cnn": cnn_actual}


def run_stage2(models: dict, stage1_actual: float, news_features: dict, market_returns: dict) -> tuple[float, float]:
    fused = {**news_features, **market_returns}
    X = np.array([[fused.get(feat, 0.0) for feat in STAGE2_FEATURE_ORDER]])
    predicted_error = float(models["correction_model"].predict(X)[0])
    final_actual = stage1_actual - predicted_error
    correction = final_actual - stage1_actual
    return final_actual, correction
