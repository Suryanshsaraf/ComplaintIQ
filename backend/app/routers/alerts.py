from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Alert
from ..schemas import AlertOut, AlertPatch
from ..services import alerts as svc
from ..services import pipeline as pl

router = APIRouter(prefix="/api/alerts", tags=["alerts"])
SEV = case({"critical": 0, "high": 1, "medium": 2, "low": 3}, value=Alert.severity, else_=4)


@router.get("", response_model=list[AlertOut])
def list_alerts(status: str | None = Query(None, pattern="^(open|investigating|acknowledged|resolved|active)$"),
                severity: str | None = Query(None, pattern="^(low|medium|high|critical)$"),
                type: str | None = None, db: Session = Depends(get_db)):
    q = select(Alert)
    if status == "active":
        q = q.where(Alert.status != "resolved")
    elif status:
        q = q.where(Alert.status == status)
    if severity:
        q = q.where(Alert.severity == severity)
    if type:
        q = q.where(Alert.type == type)
    return db.scalars(q.order_by(SEV, Alert.updated_at.desc())).all()


@router.get("/counts")
def counts(db: Session = Depends(get_db)):
    rows = db.execute(select(Alert.status, func.count()).group_by(Alert.status)).all()
    return {s: n for s, n in rows}


@router.post("/refresh")
def refresh(db: Session = Depends(get_db)):
    return pl.refresh_analytics(db)


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.get(Alert, alert_id)
    if not a:
        raise HTTPException(404, "Alert not found")
    return a


@router.patch("/{alert_id}", response_model=AlertOut)
def update_alert(alert_id: int, body: AlertPatch, db: Session = Depends(get_db)):
    a = db.get(Alert, alert_id)
    if not a:
        raise HTTPException(404, "Alert not found")
    return svc.set_status(db, a, body.status, body.note)
