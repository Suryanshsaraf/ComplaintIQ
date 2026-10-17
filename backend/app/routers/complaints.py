import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from ..db import get_db
from ..models import Complaint, ModelRun, Prediction
from ..schemas import ComplaintOut, ComplaintPage, PredictIn
from ..services import classifiers as clf
from ..services import pipeline as pl

router = APIRouter(prefix="/api", tags=["complaints"])

SORTS = {"date": Complaint.created_at, "id": Complaint.id, "category": Prediction.category,
         "sentiment": Prediction.sentiment_score, "confidence": Prediction.category_prob,
         "product": Complaint.product, "channel": Complaint.channel}


def filtered(stmt, q, date_from, date_to, category, sentiment, channel, product, topic_id=None, cluster_id=None):
    if q:
        like = f"%{q.strip().lower().replace('%', '').replace('_', ' ')}%"
        stmt = stmt.where(or_(func.lower(Complaint.text).like(like), func.lower(Complaint.external_id).like(like)))
    if date_from:
        stmt = stmt.where(Complaint.created_at >= date_from)
    if date_to:
        stmt = stmt.where(Complaint.created_at <= date_to)
    if category:
        stmt = stmt.where(Prediction.category == category)
    if sentiment:
        stmt = stmt.where(Prediction.sentiment == sentiment)
    if channel:
        stmt = stmt.where(Complaint.channel == channel)
    if product:
        stmt = stmt.where(Complaint.product == product)
    if topic_id is not None:
        stmt = stmt.where(Prediction.topic_id == topic_id)
    if cluster_id is not None:
        stmt = stmt.where(Prediction.cluster_id == cluster_id)
    return stmt


def _filters(q: str | None = None, date_from: date | None = None, date_to: date | None = None,
             category: str | None = None, sentiment: str | None = Query(None, pattern="^(negative|neutral|positive)$"),
             channel: str | None = None, product: str | None = None, topic_id: int | None = None,
             cluster_id: int | None = None):
    return dict(q=q, date_from=date_from, date_to=date_to, category=category, sentiment=sentiment, channel=channel,
                product=product, topic_id=topic_id, cluster_id=cluster_id)


@router.get("/complaints", response_model=ComplaintPage)
def list_complaints(f: dict = Depends(_filters), page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=200),
                    sort: str = Query("date"), order: str = Query("desc", pattern="^(asc|desc)$"),
                    db: Session = Depends(get_db)):
    if sort not in SORTS:
        raise HTTPException(422, f"sort must be one of {sorted(SORTS)}")
    base = filtered(select(Complaint).join(Prediction, Prediction.complaint_id == Complaint.id, isouter=True), **f)
    total = db.scalar(select(func.count()).select_from(base.order_by(None).subquery()))
    col = SORTS[sort]
    stmt = base.options(joinedload(Complaint.prediction)).order_by(col.desc() if order == "desc" else col.asc(),
                                                                   Complaint.id.desc())
    items = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).unique().all()
    return {"items": items, "total": total or 0, "page": page, "page_size": page_size}


@router.get("/complaints/export")
def export_complaints(f: dict = Depends(_filters), db: Session = Depends(get_db)):
    stmt = filtered(select(Complaint, Prediction).join(Prediction, Prediction.complaint_id == Complaint.id,
                                                       isouter=True), **f).order_by(Complaint.created_at, Complaint.id).limit(200_000)
    header = ["id", "external_id", "date", "text", "product", "channel", "true_category", "true_sentiment",
              "predicted_category", "category_probability", "predicted_sentiment", "sentiment_score", "topic_id",
              "cluster_id", "keywords", "split", "is_synthetic"]

    def rows():
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(header)
        yield buf.getvalue(); buf.seek(0); buf.truncate()
        for c, p in db.execute(stmt):
            w.writerow([c.id, c.external_id, c.created_at, c.text, c.product, c.channel, c.true_category,
                        c.true_sentiment, p and p.category, p and round(p.category_prob, 4), p and p.sentiment,
                        p and round(p.sentiment_score, 4), p and p.topic_id, p and p.cluster_id,
                        p and "; ".join(p.keywords or []), p and p.split, c.is_synthetic])
            yield buf.getvalue(); buf.seek(0); buf.truncate()

    return StreamingResponse(rows(), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=complaintiq_export.csv"})


@router.get("/complaints/filter-options")
def filter_options(db: Session = Depends(get_db)):
    def distinct(col):
        return [v for (v,) in db.execute(select(col).where(col.is_not(None)).distinct().order_by(col)).all()]
    lo, hi = db.execute(select(func.min(Complaint.created_at), func.max(Complaint.created_at))).one()
    return {"categories": distinct(Prediction.category), "sentiments": ["negative", "neutral", "positive"],
            "channels": distinct(Complaint.channel), "products": distinct(Complaint.product),
            "date_min": lo, "date_max": hi}


def _topic_cluster_info(db: Session, p: Prediction) -> dict:
    info = {}
    for kind, pid, key in (("topics", p.topic_id, "topic_id"), ("clusters", p.cluster_id, "cluster_id")):
        run = pl.latest_run(db, kind)
        if run and pid is not None:
            lst = run.result.get("topics" if kind == "topics" else "clusters", [])
            m = next((t for t in lst if t[key] == pid), None)
            if m:
                info[kind[:-1]] = {"id": pid, "terms": m["terms"][:6]}
    return info


@router.get("/complaints/{complaint_id}")
def complaint_detail(complaint_id: int, db: Session = Depends(get_db)):
    c = db.scalar(select(Complaint).options(joinedload(Complaint.prediction)).where(Complaint.id == complaint_id))
    if not c:
        raise HTTPException(404, "Complaint not found")
    out = ComplaintOut.model_validate(c).model_dump(mode="json")
    expl = {"note": "Terms that pushed the fitted model toward its prediction. This describes the model, not real-world causes."}
    if c.prediction:
        cat, sent = pl.load_artifact("category"), pl.load_artifact("sentiment")
        if cat is not None:
            expl["category_terms"] = clf.explain(cat, c.text, c.prediction.category)
        if sent is not None:
            expl["sentiment_terms"] = clf.explain(sent, c.text, c.prediction.sentiment)
        expl.update(_topic_cluster_info(db, c.prediction))
        if c.prediction.split == "train":
            expl["warning"] = "This complaint was in the training split; its prediction is in-sample."
    out["explanation"] = expl
    return out


@router.post("/predict")
def predict(body: PredictIn):
    if not pl.models_ready():
        raise HTTPException(409, "Models are not trained yet. Import labelled data or run retraining.")
    sup = pl._predict_supervised([body.text])
    cat, sent = pl.load_artifact("category"), pl.load_artifact("sentiment")
    _, _, cproba, cclasses = clf.predict_with_proba(cat, [body.text])
    kv = pl.load_artifact("keyword_vec")
    from ..services import unsupervised as uns
    kws = uns.doc_keywords(kv.transform([body.text]), kv.get_feature_names_out()) [0] if kv is not None else []
    return {"category": str(sup["category"][0]), "category_prob": float(sup["category_prob"][0]),
            "category_probabilities": {str(c): round(float(p), 4) for c, p in zip(cclasses, cproba[0])},
            "sentiment": str(sup["sentiment"][0]), "sentiment_score": float(sup["score"][0]),
            "keywords": kws, "explanation": {"category_terms": clf.explain(cat, body.text, str(sup["category"][0])),
                                             "sentiment_terms": clf.explain(sent, body.text, str(sup["sentiment"][0]))}}
