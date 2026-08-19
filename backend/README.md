# AAPL Prediction & Monitoring — Backend

FastAPI backend for the AAPL two-stage prediction pipeline (LSTM+CNN ensemble → news-aware correction), ported from the original Streamlit app into reusable services + REST APIs + independently-schedulable jobs.

## Verified working
Every endpoint and job in this backend has been run end-to-end against a seeded SQLite database as part of building it (see below) — this isn't just structurally-complete scaffolding.

## Structure
```
backend/
  app/
    main.py          FastAPI app, CORS, router registration
    config.py         All settings from environment variables
    database.py        SQLAlchemy engine/session
    models/            Prediction, Alert, FeatureSnapshot, JobRun
    schemas/            Pydantic response models
    routes/             REST endpoints (see API section below)
    services/           Orchestration: prediction pipeline, actual-price matching
    ml/                 Model loading/inference, feature engineering, news similarity
    monitoring/          Performance metrics, drift (PSI/KS), data quality, alerting
    jobs/                Standalone scripts: daily_prediction, update_actual_prices, monitoring
  requirements.txt        Full deps (includes tensorflow, chromadb, sentence-transformers)
  requirements-lite.txt    API/DB/jobs deps only — no heavy ML libs
  Dockerfile
  .env.example
```

## Local setup (no Docker, SQLite)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-lite.txt   # or requirements.txt for real predictions
cp .env.example .env

# Populate demo data so every endpoint/page works immediately:
python -m app.jobs.seed_demo_data

uvicorn app.main:app --reload
```
API docs at `http://localhost:8000/docs`. Point the frontend's `.env` at `http://localhost:8000/api` with `VITE_USE_MOCK_DATA=false`.

## Local setup (Docker Compose — Postgres + backend + frontend)
```bash
cd project-root
cp models/README.md models/  # already there — just make sure real model files land in ./models
docker compose up --build
```

## Environment variables
See `.env.example`. Nothing is hardcoded — `DATABASE_URL`, `NEWS_API_KEY`, `MODEL_DIR`, `CORS_ORIGINS`, and every monitoring threshold are all configurable.

## Database
Works against SQLite (`DATABASE_URL=sqlite:///./aapl_predictor.db`, zero setup) or PostgreSQL (`DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/db`) — same code, no branching. Tables are created automatically on startup (`init_db()`); for a real production rollout, swap in Alembic migrations.

## Running the pipeline manually
```bash
python -m app.jobs.daily_prediction        # fetch data, run model, store one prediction
python -m app.jobs.update_actual_prices    # back-fill actual prices for past predictions
python -m app.jobs.monitoring              # data-quality + drift + performance checks -> alerts
```
Each job wraps itself in a `JobRun` row (RUNNING → SUCCESS/FAILED) so `/api/monitoring/health` can report whether the latest scheduled run succeeded, and dispatches a CRITICAL alert automatically on failure — verified by intentionally running `update_actual_prices` without network access during development: it failed cleanly, logged the error, and created the alert exactly as designed.

## GitHub Actions scheduling
`.github/workflows/daily-prediction.yml` runs all three jobs once per trading day (21:30 UTC ≈ market close + buffer). Set repo secrets `DATABASE_URL` and `NEWS_API_KEY`, and optionally repo variables `MODEL_DIR`/`MODEL_VERSION`/`CORS_ORIGINS`. No in-process scheduler runs inside the FastAPI server — free-tier hosts can't be relied on to keep a process alive continuously, so scheduling lives entirely in GitHub Actions (or swap in any external cron service that can `curl` a trigger or run the same `python -m app.jobs.*` commands).

## About the model files
This backend expects the following files in `MODEL_DIR` (default `../models`, i.e. the top-level `models/` folder):
```
lstm_model.keras
cnn_model.keras
meta_model.pkl (or meta_learner.pkl)
Best_Adjustment_Model.pkl   (or your CORRECTION_MODEL_FILENAME)
feature_scaler.pkl
target_scaler.pkl
feature_scaler_raw.pkl
target_scaler_raw.pkl
```
Until these are present, `/api/monitoring/health` reports `model_file_exists: false` and `POST /api/predict` / the daily job return a clean `503 ModelNotAvailableError` rather than crashing — verified during development. Drop the real files in and everything else already works against them with zero code changes (`app/ml/model_service.py` mirrors the Streamlit app's loading logic exactly).

## API endpoints
```
GET  /api/health
GET  /api/stock/summary
GET  /api/prediction/latest
GET  /api/prediction/latest/detail
GET  /api/predictions?limit=&range=
GET  /api/predictions/{date}
GET  /api/performance?range=
GET  /api/performance/trend
GET  /api/data-quality
GET  /api/drift
GET  /api/monitoring/distribution
GET  /api/monitoring/health
GET  /api/alerts?severity=&resolved=
GET  /api/model/about
POST /api/predict
```

## Deployment (free-tier)
- **Backend**: Render / Railway / Fly.io free tier (Dockerfile provided). Note `tensorflow` is heavy — if your free tier can't fit it, either use a `tensorflow-cpu` slim wheel, convert models to ONNX/TFLite, or run the daily job in GitHub Actions (which has more headroom) and only serve the DB-read endpoints from the lightweight web dyno.
- **Database**: any free-tier Postgres (Neon, Supabase, Railway).
- **Scheduled jobs**: GitHub Actions (included) — free on public repos, generous minutes on private.
- **Frontend**: static host (Vercel/Netlify/Cloudflare Pages) — see `frontend/README.md`.

## Troubleshooting
- **`ModelNotAvailableError`**: model files missing from `MODEL_DIR` — expected until you add them.
- **`MarketDataError` / 502 from `/api/predict`**: Yahoo Finance unreachable or returned empty/NaN data — this is the same defensive validation the original Streamlit app had, ported as-is.
- **`insufficient_data: true` on `/api/performance`**: no predictions with a matched actual price yet in that range — run `seed_demo_data` or wait for the pipeline to accumulate history.
- **Drift page shows "Insufficient history"**: needs ≥90 days of `FeatureSnapshot` rows; the seed script provides these.
