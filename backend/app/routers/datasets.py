import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..config import SYNTHETIC_ROWS
from ..db import get_db
from ..models import Complaint, ImportJob
from ..services import datasets as ds
from ..services import pipeline as pl

router = APIRouter(prefix="/api", tags=["datasets"])
MAX_BYTES = 25 * 1024 * 1024


async def _read(file: UploadFile):
    raw = await file.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, "File too large (max 25 MB).")
    try:
        return ds.read_csv_bytes(raw)
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@router.post("/imports/preview")
async def preview(file: UploadFile = File(...)):
    return ds.preview(await _read(file))


@router.post("/imports")
async def import_csv(file: UploadFile = File(...), mapping: str = Form(...), db: Session = Depends(get_db)):
    try:
        mp = json.loads(mapping)
        assert isinstance(mp, dict)
    except Exception:
        raise HTTPException(422, "mapping must be a JSON object of field -> column")
    df = await _read(file)
    try:
        job, ids = ds.import_dataframe(db, df, mp, file.filename or "upload.csv")
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    scored = pl.infer_new(db, ids) if ids else 0
    analytics = pl.refresh_analytics(db) if ids else {"status": "no_new_rows"}
    return {"import_id": job.id, "summary": job.summary, "scored": scored, "models_ready": pl.models_ready(),
            "analytics": analytics}


@router.get("/imports")
def list_imports(db: Session = Depends(get_db)):
    return [{"id": j.id, "filename": j.filename, "status": j.status, "summary": j.summary, "mapping": j.mapping,
             "created_at": j.created_at} for j in db.scalars(select(ImportJob).order_by(ImportJob.id.desc()).limit(50))]


@router.get("/datasets/stats")
def stats(db: Session = Depends(get_db)):
    return ds.dataset_stats(db)


@router.delete("/datasets/synthetic")
def delete_synthetic(db: Session = Depends(get_db)):
    n = db.execute(delete(Complaint).where(Complaint.is_synthetic.is_(True))).rowcount
    db.commit()
    return {"deleted": n, "analytics": pl.refresh_analytics(db)}


@router.post("/datasets/synthetic")
def reseed_synthetic(rows: int = SYNTHETIC_ROWS, db: Session = Depends(get_db)):
    if not 500 <= rows <= 20000:
        raise HTTPException(422, "rows must be between 500 and 20000")
    ds.seed_synthetic(db, rows)
    return pl.train_all(db)
