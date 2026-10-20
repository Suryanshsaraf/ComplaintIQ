import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, select

from .config import AUTO_BOOTSTRAP, CORS_ORIGINS, SYNTHETIC_ROWS
from .db import SessionLocal, init_db
from .models import Complaint
from .routers import alerts, complaints, dashboard, datasets, intelligence
from .services import datasets as ds
from .services import pipeline as pl

log = logging.getLogger("complaintiq")


def bootstrap(db=None, rows: int = SYNTHETIC_ROWS):
    """Seed synthetic data and train everything when the database is empty."""
    own = db is None
    db = db or SessionLocal()
    try:
        if (db.scalar(select(func.count(Complaint.id))) or 0) == 0:
            log.info("Empty database: seeding %s synthetic complaints and training models...", rows)
            ds.seed_synthetic(db, rows)
            return pl.train_all(db)
        if not pl.models_ready():
            return pl.train_all(db)
    finally:
        if own:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if AUTO_BOOTSTRAP:
        bootstrap()
    yield


app = FastAPI(title="ComplaintIQ API", version="1.0.0", lifespan=lifespan,
              description="Customer complaint intelligence: NLP classification, topics, clustering, anomaly "
                          "detection, forecasting and alerting. Bundled data is synthetic.")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_origin_regex=r"^https?://.*", allow_methods=["*"], allow_headers=["*"])
for r in (dashboard, complaints, intelligence, alerts, datasets):
    app.include_router(r.router)


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):
    log.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": f"Internal error: {type(exc).__name__}"})


@app.get("/api/health", tags=["system"])
def health():
    with SessionLocal() as db:
        n = db.scalar(select(func.count(Complaint.id))) or 0
    return {"status": "ok", "complaints": n, "models_ready": pl.models_ready()}
