# Model files

Place your trained model artifacts here (this directory is mounted read-only
into the backend container via `docker-compose.yml`, and is `MODEL_DIR`'s
default target — `../models` relative to `backend/`).

Expected files (from the original Streamlit app):
```
lstm_model.keras
cnn_model.keras
meta_model.pkl              (or meta_learner.pkl)
Best_Adjustment_Model.pkl   (or set CORRECTION_MODEL_FILENAME to match yours)
feature_scaler.pkl
target_scaler.pkl
feature_scaler_raw.pkl
target_scaler_raw.pkl
```

Until these exist, the backend runs normally — every read endpoint (history,
performance, monitoring, alerts) works against stored predictions — but
`POST /api/predict` and the daily prediction job will return a clean
`ModelNotAvailableError` (HTTP 503) instead of generating a prediction.
