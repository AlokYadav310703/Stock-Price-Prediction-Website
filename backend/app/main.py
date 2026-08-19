import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routes import alerts, health, model_info, monitoring, performance, predict, prediction, predictions, stock

settings = get_settings()

logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("app.main")

app = FastAPI(title=settings.APP_NAME, version=settings.MODEL_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("%s started (env=%s)", settings.APP_NAME, settings.ENVIRONMENT)


API_PREFIX = "/api"
app.include_router(health.router, prefix=API_PREFIX)
app.include_router(stock.router, prefix=API_PREFIX)
app.include_router(prediction.router, prefix=API_PREFIX)
app.include_router(predict.router, prefix=API_PREFIX)
app.include_router(predictions.router, prefix=API_PREFIX)
app.include_router(performance.router, prefix=API_PREFIX)
app.include_router(monitoring.router, prefix=API_PREFIX)
app.include_router(alerts.router, prefix=API_PREFIX)
app.include_router(model_info.router, prefix=API_PREFIX)


@app.get("/")
def root():
    return {"service": settings.APP_NAME, "status": "ok", "docs": "/docs"}
