"""NLP + ML intelligence endpoints (read stored model results; nothing is retrained per request)."""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Anomaly, Complaint, EvaluationResult, ModelRun, Prediction
from ..services import pipeline as pl

router = APIRouter(prefix="/api", tags=["intelligence"])


def _sent_stats(db, group_col, extra=None):
    q = (select(group_col, func.count(), func.avg(Prediction.sentiment_score),
                func.sum(case((Prediction.sentiment == "negative", 1), else_=0)),
                func.sum(case((Prediction.sentiment == "neutral", 1), else_=0)),
                func.sum(case((Prediction.sentiment == "positive", 1), else_=0)))
         .select_from(Prediction).join(Complaint, Complaint.id == Prediction.complaint_id).group_by(group_col))
    return [{"key": "Unknown" if k is None else k, "count": n, "avg_sentiment": round(float(a or 0), 3), "negative": int(ng or 0),
             "neutral": int(nu or 0), "positive": int(po or 0)} for k, n, a, ng, nu, po in db.execute(q).all()]


# ------------------------------------------------------------------ NLP
@router.get("/nlp/sentiment")
def sentiment_overview(db: Session = Depends(get_db)):
    return {"overall": _sent_stats(db, Prediction.sentiment), "by_category": _sent_stats(db, Prediction.category),
            "by_channel": _sent_stats(db, Complaint.channel), "by_product": _sent_stats(db, Complaint.product)}


@router.get("/nlp/evaluation")
def nlp_evaluation(task: str = Query("category", pattern="^(category|sentiment)$"), db: Session = Depends(get_db)):
    run = pl.latest_run(db, task)
    if not run:
        return {"status": "unavailable", "reason": "No supervised model trained (needs labelled data).", "models": []}
    rows = db.scalars(select(EvaluationResult).where(EvaluationResult.model_run_id == run.id)
                      .order_by(EvaluationResult.f1_macro.desc())).all()
    models = []
    for r in rows:
        pc = dict(r.per_class)
        cal = pc.pop("_calibration", None)
        models.append({"model_name": r.model_name, "is_selected": r.is_selected, "accuracy": r.accuracy,
                       "precision_macro": r.precision_macro, "recall_macro": r.recall_macro, "f1_macro": r.f1_macro,
                       "cv_f1_macro": r.cv_f1_macro, "labels": r.labels, "confusion": r.confusion, "per_class": pc,
                       "calibration": cal, "n_train": r.n_train, "n_test": r.n_test})
    return {"status": "ok", "task": task, "trained_at": run.created_at, "selected": run.name, "models": models,
            "influential_terms": run.result.get("influential_terms", {}),
            "protocol": "80/20 stratified hold-out; TF-IDF fitted inside the pipeline on training data only; "
                        "model selection by 5-fold CV macro-F1 on the training split; test split used only for reporting."}


@router.get("/nlp/topics")
def topics(db: Session = Depends(get_db)):
    run = pl.latest_run(db, "topics")
    if not run:
        return {"status": "unavailable", "topics": []}
    stats = {r["key"]: r for r in _sent_stats(db, Prediction.topic_id)}
    cat_rows = db.execute(select(Prediction.topic_id, Prediction.category, func.count()).group_by(Prediction.topic_id, Prediction.category)).all()
    cats: dict = {}
    for t, c, n in cat_rows:
        cats.setdefault(t, {})[c] = n
    total = sum(s["count"] for s in stats.values()) or 1
    as_of = db.scalar(select(func.max(Complaint.created_at)))
    weekly = {}
    if as_of:
        start = as_of - timedelta(days=83)
        for t, d, n in db.execute(select(Prediction.topic_id, func.min(Complaint.created_at), func.count())
                                  .join(Complaint, Complaint.id == Prediction.complaint_id).where(Complaint.created_at >= start)
                                  .group_by(Prediction.topic_id, func.strftime("%Y-%W", Complaint.created_at)
                                            if db.bind.dialect.name == "sqlite" else func.to_char(Complaint.created_at, "IYYY-IW"))).all():
            weekly.setdefault(t, []).append({"week": d, "count": n})
    out = []
    for t in run.result["topics"]:
        s = stats.get(t["topic_id"], {"count": 0, "avg_sentiment": 0, "negative": 0, "neutral": 0, "positive": 0})
        out.append({**{k: t[k] for k in ("topic_id", "label", "terms", "representatives")}, "count": s["count"],
                    "share": s["count"] / total, "avg_sentiment": s["avg_sentiment"],
                    "sentiment": {k: s[k] for k in ("negative", "neutral", "positive")},
                    "top_categories": sorted(cats.get(t["topic_id"], {}).items(), key=lambda x: -x[1])[:3],
                    "weekly": sorted(weekly.get(t["topic_id"], []), key=lambda w: w["week"])})
    return {"status": "ok", "algorithm": run.name, "topics": sorted(out, key=lambda t: -t["count"]),
            "trained_at": run.created_at}


@router.get("/nlp/keywords")
def keywords(category: str | None = None, db: Session = Depends(get_db)):
    run = pl.latest_run(db, "keywords")
    if not run:
        return {"status": "unavailable", "keywords": []}
    if not category:
        return {"status": "ok", "keywords": run.result["global"]}
    # keyword frequency within a predicted category (from stored per-document keywords)
    counts: dict = {}
    for (kws,) in db.execute(select(Prediction.keywords).where(Prediction.category == category)).all():
        for k in kws or []:
            counts[k] = counts.get(k, 0) + 1
    top = sorted(counts.items(), key=lambda x: -x[1])[:25]
    return {"status": "ok", "category": category, "keywords": [{"term": k, "docs": n} for k, n in top]}


# ------------------------------------------------------------------ ML
@router.get("/ml/clusters")
def clusters(db: Session = Depends(get_db)):
    run = pl.latest_run(db, "clusters")
    if not run:
        return {"status": "unavailable", "clusters": []}
    stats = {r["key"]: r for r in _sent_stats(db, Prediction.cluster_id)}
    cat_rows = db.execute(select(Prediction.cluster_id, Prediction.category, func.count())
                          .group_by(Prediction.cluster_id, Prediction.category)).all()
    cats: dict = {}
    for c, k, n in cat_rows:
        cats.setdefault(c, {})[k] = n
    total = sum(s["count"] for s in stats.values()) or 1
    out = []
    for c in run.result["clusters"]:
        s = stats.get(c["cluster_id"], {"count": 0, "avg_sentiment": 0, "negative": 0, "neutral": 0, "positive": 0})
        out.append({"cluster_id": c["cluster_id"], "terms": c["terms"], "representatives": c["representatives"],
                    "size": s["count"], "share": s["count"] / total, "avg_sentiment": s["avg_sentiment"],
                    "sentiment": {k: s[k] for k in ("negative", "neutral", "positive")},
                    "categories": sorted(cats.get(c["cluster_id"], {}).items(), key=lambda x: -x[1])[:4]})
    return {"status": "ok", "algorithm": run.name, "k": run.result["k"], "silhouette": run.result["silhouette"],
            "k_scan": run.result["k_scan"], "points": run.result["points"], "clusters": out,
            "vs_ground_truth": run.result.get("vs_ground_truth"), "trained_at": run.created_at}


@router.get("/ml/anomalies")
def anomalies(days: int = Query(120, ge=14, le=730), method: str | None = Query(None, pattern="^(rolling_zscore|isolation_forest)$"),
              db: Session = Depends(get_db)):
    run = pl.latest_run(db, "anomalies")
    if not run or run.result.get("status") != "ok":
        return {"status": "insufficient_data", "reason": "At least ~5 weeks of dated complaints are required.",
                "anomalies": [], "daily": []}
    as_of = db.scalar(select(func.max(Complaint.created_at)))
    start = as_of - timedelta(days=days - 1)
    q = select(Anomaly).where(Anomaly.day >= start).order_by(Anomaly.day.desc(), Anomaly.score.desc())
    if method:
        q = q.where(Anomaly.method == method)
    rows = db.scalars(q).all()
    daily = [d for d in run.result["daily"] if d["day"] >= start.isoformat()]
    return {"status": "ok", "summary": run.result["summary"], "daily": daily, "trained_at": run.created_at,
            "anomalies": [{"id": a.id, "day": a.day, "method": a.method, "score": round(a.score, 2), "category": a.category,
                           "triggers": a.triggers, "metrics": a.metrics, "explanation": a.explanation} for a in rows]}


@router.get("/ml/forecast")
def forecast(horizon: int = Query(14, description="7, 14 or 30 days", ge=1, le=30), db: Session = Depends(get_db)):
    if horizon not in (7, 14, 30):
        raise HTTPException(422, "horizon must be 7, 14 or 30")
    run = pl.latest_run(db, "forecast")
    if not run:
        return {"status": "insufficient_data", "reason": "No forecast available yet."}
    r = dict(run.result)
    if r.get("status") == "ok":
        r["forecast"] = r["forecast"][:horizon]
        r["horizon"] = horizon
    return r


@router.get("/ml/emerging")
def emerging(db: Session = Depends(get_db)):
    run = pl.latest_run(db, "emerging")
    return run.result if run else {"status": "unavailable", "issues": []}


@router.get("/models/runs")
def model_runs(db: Session = Depends(get_db)):
    rows = db.scalars(select(ModelRun).order_by(ModelRun.id.desc()).limit(60)).all()
    return [{"id": r.id, "kind": r.kind, "name": r.name, "n_rows": r.n_rows, "is_active": r.is_active,
             "created_at": r.created_at} for r in rows]


@router.post("/models/retrain")
def retrain(db: Session = Depends(get_db)):
    """Explicit, user-triggered retraining on all data currently in the database."""
    return pl.train_all(db)
