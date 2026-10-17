"""Orchestrates training, inference and analytics refresh against the database.

* `train_all`    - fit all models on the data currently in the DB, persist artifacts + results, write predictions.
* `infer_new`    - score newly imported rows with the stored models (no retraining).
* `refresh_analytics` - recompute anomalies, forecast, emerging terms and alerts (cheap, no model fitting of NLP).
"""
import hashlib
import json
from datetime import date, datetime

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from ..config import ARTIFACT_DIR
from ..models import Anomaly, Complaint, EvaluationResult, ModelRun, Prediction
from . import alerts as alert_service
from . import classifiers as clf
from . import timeseries as ts
from . import unsupervised as uns
from .nlp import clean_text

ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
_cache: dict = {}


def sanitize(obj):
    """Recursively replace NaN/inf with None so results are valid JSON."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (float, np.floating)):
        return float(obj) if np.isfinite(obj) else None
    if isinstance(obj, np.integer):
        return int(obj)
    return obj


def text_hash(text: str) -> str:
    return hashlib.sha1(clean_text(text).encode()).hexdigest()


# ---------------------------------------------------------------- artifact registry
def save_artifact(name: str, obj) -> None:
    joblib.dump(obj, ARTIFACT_DIR / f"{name}.joblib")
    _cache[name] = obj


def load_artifact(name: str):
    if name not in _cache:
        p = ARTIFACT_DIR / f"{name}.joblib"
        if not p.exists():
            return None
        _cache[name] = joblib.load(p)
    return _cache[name]


def models_ready() -> bool:
    return load_artifact("category") is not None and load_artifact("sentiment") is not None


def latest_run(db: Session, kind: str) -> ModelRun | None:
    return db.scalar(select(ModelRun).where(ModelRun.kind == kind, ModelRun.is_active.is_(True))
                     .order_by(ModelRun.id.desc()))


def _new_run(db: Session, kind: str, name: str, result: dict, n_rows: int, params: dict | None = None) -> ModelRun:
    db.execute(update(ModelRun).where(ModelRun.kind == kind).values(is_active=False))
    run = ModelRun(kind=kind, name=name, result=sanitize(result), n_rows=n_rows, params=params or {})
    db.add(run)
    db.flush()
    return run


def load_frame(db: Session) -> pd.DataFrame:
    rows = db.execute(select(Complaint.id, Complaint.text, Complaint.created_at, Complaint.true_category,
                             Complaint.true_sentiment).order_by(Complaint.id)).all()
    return pd.DataFrame(rows, columns=["id", "text", "day", "true_category", "true_sentiment"])


def analytics_frame(db: Session) -> pd.DataFrame:
    rows = db.execute(select(Complaint.id, Complaint.text, Complaint.created_at, Prediction.category,
                             Prediction.sentiment, Prediction.sentiment_score)
                      .join(Prediction, Prediction.complaint_id == Complaint.id)).all()
    return pd.DataFrame(rows, columns=["id", "text", "day", "category", "sentiment", "score"])


# ---------------------------------------------------------------- prediction helpers
def _predict_supervised(texts: list[str]) -> dict:
    cat, sent = load_artifact("category"), load_artifact("sentiment")
    n = len(texts)
    out = {"category": np.array(["Other"] * n, dtype=object), "category_prob": np.zeros(n),
           "sentiment": np.array(["neutral"] * n, dtype=object), "score": np.zeros(n)}
    if cat is not None and n:
        c, p, _, _ = clf.predict_with_proba(cat, texts)
        out["category"], out["category_prob"] = c, p
    elif n:
        out["category"] = np.array(["Unclassified"] * n, dtype=object)
    if sent is not None and n:
        s, _, proba, classes = clf.predict_with_proba(sent, texts)
        out["sentiment"] = s
        pos = proba[:, list(classes).index("positive")] if "positive" in classes else 0
        neg = proba[:, list(classes).index("negative")] if "negative" in classes else 0
        out["score"] = pos - neg
    return out


def infer_new(db: Session, complaint_ids: list[int]) -> int:
    """Predict category/sentiment/topic/cluster/keywords for specific rows using stored models."""
    if not complaint_ids:
        return 0
    rows = db.execute(select(Complaint.id, Complaint.text).where(Complaint.id.in_(complaint_ids))).all()
    ids, texts = [r[0] for r in rows], [r[1] for r in rows]
    sup = _predict_supervised(texts)
    topic = load_artifact("topics")
    topic_ids = uns.assign_topics(topic, texts) if topic else [None] * len(texts)
    kv, cl = load_artifact("keyword_vec"), load_artifact("clusters")
    kws = [[] for _ in texts]
    cluster_ids = [None] * len(texts)
    if kv is not None:
        X = kv.transform(texts)
        kws = uns.doc_keywords(X, kv.get_feature_names_out())
        if cl is not None:
            cluster_ids = uns.assign_clusters(cl, X)
    db.execute(delete(Prediction).where(Prediction.complaint_id.in_(ids)))
    db.bulk_insert_mappings(Prediction, [{
        "complaint_id": ids[i], "category": str(sup["category"][i]), "category_prob": float(sup["category_prob"][i]),
        "sentiment": str(sup["sentiment"][i]), "sentiment_score": float(sup["score"][i]),
        "topic_id": None if topic_ids[i] is None else int(topic_ids[i]),
        "cluster_id": None if cluster_ids[i] is None else int(cluster_ids[i]),
        "keywords": kws[i], "split": "external", "model_run_id": None} for i in range(len(ids))])
    db.commit()
    return len(ids)


# ---------------------------------------------------------------- training
def _store_eval(db: Session, run: ModelRun, task: str, results: list[dict]) -> None:
    for r in results:
        db.add(EvaluationResult(
            model_run_id=run.id, task=task, model_name=r["model_name"], is_selected=r["is_selected"],
            accuracy=r["accuracy"], precision_macro=r["precision_macro"], recall_macro=r["recall_macro"],
            f1_macro=r["f1_macro"], cv_f1_macro=r.get("cv_f1_macro"), labels=r["labels"], confusion=r["confusion"],
            per_class={**r["per_class"], **({"_calibration": {"mean_confidence": r["mean_confidence"], "ece": r["ece"]}}
                                            if "ece" in r else {})},
            n_train=r["n_train"], n_test=r["n_test"]))


def train_all(db: Session) -> dict:
    df = load_frame(db)
    if df.empty:
        return {"status": "empty", "message": "No complaints in the database; import data first."}
    texts = df["text"].tolist()
    report: dict = {"n_rows": len(df), "tasks": {}}
    split = np.array(["external"] * len(df), dtype=object)

    for task, col in (("category", "true_category"), ("sentiment", "true_sentiment")):
        labeled = df[col].notna().values
        if labeled.sum() == 0:
            report["tasks"][task] = {"status": "skipped", "reason": "no ground-truth labels"}
            continue
        idx = np.where(labeled)[0]
        out = clf.train_classifier([texts[i] for i in idx], df[col].iloc[idx].tolist())
        if out is None:
            report["tasks"][task] = {"status": "skipped", "reason": "too few labelled rows/classes to train"}
            continue
        save_artifact(task, out["pipeline"])
        run = _new_run(db, task, out["selected"], {"selected": out["selected"], "labels": out["labels"],
                                                   "influential_terms": clf.influential_terms(out["pipeline"])},
                       int(len(idx)))
        _store_eval(db, run, task, out["results"])
        if task == "category":  # train/test membership is reported from the category task
            split[idx[out["is_train"]]] = "train"
            split[idx[out["is_test"]]] = "test"
        sel = next(r for r in out["results"] if r["is_selected"])
        report["tasks"][task] = {"status": "ok", "selected": out["selected"], "accuracy": sel["accuracy"],
                                 "f1_macro": sel["f1_macro"]}

    sup = _predict_supervised(texts)

    # --- unsupervised models (fit on all text; no labels involved)
    topic = uns.fit_topics(texts)
    kv = uns.make_keyword_vec()
    X = kv.fit_transform(texts)
    names = kv.get_feature_names_out()
    kws = uns.doc_keywords(X, names)
    save_artifact("keyword_vec", kv)
    cl = uns.fit_clusters(texts, X, names)

    if topic:
        save_artifact("topics", {"vec": topic["vec"], "nmf": topic["nmf"]})
        topics_out = []
        for t in topic["topics"]:
            topics_out.append({**t, "representatives": [{"id": int(df["id"].iloc[i]), "text": texts[i]}
                                                        for i in t["representative_idx"]]})
        _new_run(db, "topics", "NMF (TF-IDF)", {"topics": topics_out, "k": len(topics_out),
                                                "reconstruction_err": topic["reconstruction_err"]}, len(df))
    if cl:
        save_artifact("clusters", {"svd": cl["svd"], "kmeans": cl["kmeans"]})
        res = {"k": cl["k"], "silhouette": cl["silhouette"], "k_scan": cl["scan"], "points": cl["points"],
               "clusters": [{**c, "representatives": [{"id": int(df["id"].iloc[i]), "text": texts[i]}
                                                      for i in c["representative_idx"]]} for c in cl["clusters"]],
               "vs_ground_truth": uns.cluster_vs_labels(cl["labels"], [None if pd.isna(v) else v
                                                                       for v in df["true_category"]])}
        _new_run(db, "clusters", f"KMeans (k={cl['k']}) on TF-IDF+SVD", res, len(df))
    _new_run(db, "keywords", "TF-IDF keywords", {"global": uns.global_keywords(X, names)}, len(df))

    # --- write predictions
    db.execute(delete(Prediction))
    db.bulk_insert_mappings(Prediction, [{
        "complaint_id": int(df["id"].iloc[i]), "category": str(sup["category"][i]),
        "category_prob": float(sup["category_prob"][i]), "sentiment": str(sup["sentiment"][i]),
        "sentiment_score": float(sup["score"][i]),
        "topic_id": int(topic["assignment"][i]) if topic else None,
        "cluster_id": int(cl["labels"][i]) if cl else None, "keywords": kws[i], "split": str(split[i]),
        "model_run_id": None} for i in range(len(df))])
    db.commit()
    report["analytics"] = refresh_analytics(db)
    return report


# ---------------------------------------------------------------- analytics refresh
def refresh_analytics(db: Session) -> dict:
    df = analytics_frame(db)
    if df.empty:
        db.execute(delete(Anomaly))
        db.commit()
        return {"status": "empty"}
    as_of = df["day"].max()
    an = ts.detect_anomalies(df)
    db.execute(delete(Anomaly))
    run = _new_run(db, "anomalies", "Rolling robust z-score + Isolation Forest",
                   {k: an.get(k) for k in ("status", "summary", "daily", "category_z")}, len(df))
    for a in an["anomalies"]:
        db.add(Anomaly(day=a["day"], method=a["method"], score=a["score"], metrics=sanitize(a["metrics"]),
                       triggers=a["triggers"], explanation=a["explanation"], category=a["category"],
                       model_run_id=run.id))
    fc = ts.forecast_volume(df)
    _new_run(db, "forecast", fc.get("selected_model", "n/a"), fc, len(df))
    em = ts.emerging_terms(df, as_of)
    _new_run(db, "emerging", "Recent vs baseline document frequency", em, len(df))
    db.commit()
    created = alert_service.refresh_alerts(db, df, an, fc, em, as_of)
    return {"status": "ok", "as_of": as_of.isoformat(), "anomalies": len(an["anomalies"]), "alerts": created,
            "forecast_status": fc.get("status")}
