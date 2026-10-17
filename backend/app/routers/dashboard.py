from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Alert, Anomaly, Complaint, Prediction
from ..services import pipeline as pl
from ..services.datasets import dataset_stats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
SEV_ORDER = case({"critical": 0, "high": 1, "medium": 2, "low": 3}, value=Alert.severity, else_=4)


def _as_of(db):
    return db.scalar(select(func.max(Complaint.created_at)))


def _period(db: Session, start, end) -> dict:
    n, neg, avg = db.execute(
        select(func.count(Complaint.id), func.sum(case((Prediction.sentiment == "negative", 1), else_=0)),
               func.avg(Prediction.sentiment_score))
        .join(Prediction, Prediction.complaint_id == Complaint.id)
        .where(Complaint.created_at >= start, Complaint.created_at <= end)).one()
    n = n or 0
    return {"total": n, "negative": int(neg or 0), "negative_pct": (neg or 0) / n * 100 if n else 0.0,
            "avg_sentiment": float(avg or 0.0)}


def _change(cur, prev):
    return None if not prev else round((cur - prev) / prev * 100, 1)


@router.get("/summary")
def summary(days: int = Query(30, ge=7, le=180), db: Session = Depends(get_db)):
    as_of = _as_of(db)
    if as_of is None:
        return {"empty": True, "data": dataset_stats(db)}
    cur_start = as_of - timedelta(days=days - 1)
    prev_end, prev_start = cur_start - timedelta(days=1), cur_start - timedelta(days=days)
    cur, prev = _period(db, cur_start, as_of), _period(db, prev_start, prev_end)
    active = db.execute(select(func.count(Alert.id), func.sum(case((Alert.severity.in_(["critical", "high"]), 1), else_=0)))
                        .where(Alert.status != "resolved")).one()

    def dist(col, start, end):
        rows = db.execute(select(col, func.count(Complaint.id)).join(Prediction, Prediction.complaint_id == Complaint.id)
                          .where(Complaint.created_at >= start, Complaint.created_at <= end).group_by(col)).all()
        return {k or "Unknown": v for k, v in rows}

    cat_cur, cat_prev = dist(Prediction.category, cur_start, as_of), dist(Prediction.category, prev_start, prev_end)
    sent = dist(Prediction.sentiment, cur_start, as_of)
    chan = dist(Complaint.channel, cur_start, as_of)

    # topics: stored term lists + live counts for the period
    topic_run = pl.latest_run(db, "topics")
    topics = []
    if topic_run:
        tc = dict(db.execute(select(Prediction.topic_id, func.count()).join(Complaint, Complaint.id == Prediction.complaint_id)
                             .where(Complaint.created_at >= cur_start).group_by(Prediction.topic_id)).all())
        tp = dict(db.execute(select(Prediction.topic_id, func.count()).join(Complaint, Complaint.id == Prediction.complaint_id)
                             .where(Complaint.created_at >= prev_start, Complaint.created_at <= prev_end)
                             .group_by(Prediction.topic_id)).all())
        for t in topic_run.result["topics"]:
            topics.append({"topic_id": t["topic_id"], "label": t["label"], "terms": t["terms"][:5],
                           "count": tc.get(t["topic_id"], 0), "prev_count": tp.get(t["topic_id"], 0),
                           "change_pct": _change(tc.get(t["topic_id"], 0), tp.get(t["topic_id"], 0))})
        topics.sort(key=lambda t: -t["count"])
    kw = pl.latest_run(db, "keywords")
    em = pl.latest_run(db, "emerging")
    anomalies = db.scalars(select(Anomaly).where(Anomaly.day >= as_of - timedelta(days=30))
                           .order_by(Anomaly.day.desc(), Anomaly.score.desc()).limit(12)).all()
    alerts = db.scalars(select(Alert).where(Alert.status != "resolved").order_by(SEV_ORDER, Alert.updated_at.desc()).limit(5)).all()
    fc = pl.latest_run(db, "forecast")
    return {
        "empty": False, "as_of": as_of, "days": days, "data": dataset_stats(db),
        "kpis": {
            "total": {"value": cur["total"], "prev": prev["total"], "change_pct": _change(cur["total"], prev["total"])},
            "negative_pct": {"value": round(cur["negative_pct"], 1), "prev": round(prev["negative_pct"], 1),
                             "change_pts": round(cur["negative_pct"] - prev["negative_pct"], 1)},
            "avg_sentiment": {"value": round(cur["avg_sentiment"], 3), "prev": round(prev["avg_sentiment"], 3),
                              "change": round(cur["avg_sentiment"] - prev["avg_sentiment"], 3)},
            "active_alerts": {"value": active[0] or 0, "critical_high": int(active[1] or 0)}},
        "categories": [{"category": c, "count": n, "prev_count": cat_prev.get(c, 0),
                        "change_pct": _change(n, cat_prev.get(c, 0))} for c, n in sorted(cat_cur.items(), key=lambda x: -x[1])],
        "sentiment": [{"sentiment": s, "count": sent.get(s, 0)} for s in ("negative", "neutral", "positive")],
        "channels": [{"channel": c, "count": n} for c, n in sorted(chan.items(), key=lambda x: -x[1])],
        "topics": topics[:8], "keywords": (kw.result["global"][:15] if kw else []),
        "emerging": (em.result.get("issues", []) if em else []),
        "anomalies": [{"id": a.id, "day": a.day, "method": a.method, "score": round(a.score, 2), "category": a.category,
                       "explanation": a.explanation, "triggers": a.triggers} for a in anomalies],
        "priority_alerts": [{"id": a.id, "type": a.type, "severity": a.severity, "title": a.title, "status": a.status,
                             "categories": a.categories, "explanation": a.explanation} for a in alerts],
        "forecast": ({"status": fc.result.get("status"), "selected_model": fc.result.get("selected_model"),
                      "history": fc.result.get("history", [])[-60:], "forecast": fc.result.get("forecast", [])[:14],
                      "reason": fc.result.get("reason")} if fc else None)}


@router.get("/trends")
def trends(days: int = Query(90, ge=7, le=730), granularity: str = Query("day", pattern="^(day|week)$"),
           db: Session = Depends(get_db)):
    as_of = _as_of(db)
    if as_of is None:
        return {"empty": True, "series": [], "by_category": []}
    start = as_of - timedelta(days=days - 1)
    bucket = Complaint.created_at if granularity == "day" else func.strftime("%Y-%W", Complaint.created_at) \
        if db.bind.dialect.name == "sqlite" else func.to_char(Complaint.created_at, "IYYY-IW")
    q = (select(bucket.label("b"), func.min(Complaint.created_at).label("d"), func.count(Complaint.id),
                func.sum(case((Prediction.sentiment == "negative", 1), else_=0)), func.avg(Prediction.sentiment_score))
         .join(Prediction, Prediction.complaint_id == Complaint.id).where(Complaint.created_at >= start)
         .group_by(bucket).order_by(func.min(Complaint.created_at)))
    series = [{"date": d, "total": n, "negative": int(neg or 0), "avg_sentiment": round(float(avg or 0), 3)}
              for _, d, n, neg, avg in db.execute(q).all()]
    qc = (select(bucket.label("b"), func.min(Complaint.created_at).label("d"), Prediction.category, func.count())
          .join(Prediction, Prediction.complaint_id == Complaint.id).where(Complaint.created_at >= start)
          .group_by(bucket, Prediction.category).order_by(func.min(Complaint.created_at)))
    rows: dict = {}
    for b, d, cat, n in db.execute(qc).all():
        rows.setdefault(b, {"date": d})[cat] = n
    return {"empty": False, "granularity": granularity, "series": series, "by_category": list(rows.values())}
