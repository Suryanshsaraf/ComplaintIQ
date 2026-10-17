"""CSV import (column mapping, validation, dedup, missing-value report) and synthetic-data seeding."""
import io
from datetime import date

import pandas as pd
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..config import CATEGORIES
from ..models import Complaint, ImportJob
from . import datagen
from .pipeline import text_hash

MAX_ROWS = 200_000
FIELDS = ["text", "date", "category", "sentiment", "product", "channel", "external_id"]
ALIASES = {
    "text": ["text", "complaint", "complaint_text", "description", "message", "comment", "narrative", "body",
             "consumer_complaint_narrative", "review"],
    "date": ["date", "created_at", "created", "timestamp", "submitted", "date_received", "complaint_date", "time"],
    "category": ["category", "label", "issue", "type", "true_category", "topic", "department"],
    "sentiment": ["sentiment", "true_sentiment", "polarity"],
    "product": ["product", "item", "product_name", "sub_product"],
    "channel": ["channel", "source", "submitted_via", "medium"],
    "external_id": ["id", "complaint_id", "external_id", "ticket", "ticket_id", "case_id"],
}
SENT_MAP = {"negative": "negative", "neg": "negative", "-1": "negative", "bad": "negative",
            "neutral": "neutral", "neu": "neutral", "0": "neutral", "mixed": "neutral",
            "positive": "positive", "pos": "positive", "1": "positive", "good": "positive"}


def read_csv_bytes(raw: bytes) -> pd.DataFrame:
    if not raw.strip():
        raise ValueError("The uploaded file is empty.")
    for enc in ("utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(io.BytesIO(raw), dtype=str, keep_default_na=False, encoding=enc, nrows=MAX_ROWS + 1)
            break
        except UnicodeDecodeError:
            continue
        except (pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
            raise ValueError(f"Could not parse CSV: {exc}") from exc
    else:
        raise ValueError("Could not decode the file (use UTF-8 CSV).")
    if len(df) > MAX_ROWS:
        raise ValueError(f"File has more than {MAX_ROWS:,} rows.")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def suggest_mapping(columns: list[str]) -> dict:
    low = {c.lower().replace(" ", "_"): c for c in columns}
    out: dict = {}
    for field, names in ALIASES.items():
        out[field] = next((low[n] for n in names if n in low), None)
    return out


def preview(df: pd.DataFrame) -> dict:
    blanks = {c: int((df[c].str.strip() == "").sum()) for c in df.columns}
    return {"n_rows": int(len(df)), "columns": list(df.columns), "suggested_mapping": suggest_mapping(list(df.columns)),
            "sample": df.head(8).to_dict(orient="records"), "blank_counts": blanks}


def _norm_category(v: str) -> tuple[str | None, bool]:
    v = (v or "").strip()
    if not v:
        return None, False
    for c in CATEGORIES:
        if v.lower() == c.lower():
            return c, False
    return "Other", True


def import_dataframe(db: Session, df: pd.DataFrame, mapping: dict, filename: str, synthetic: bool = False) -> tuple[ImportJob, list[int]]:
    mapping = {k: v for k, v in mapping.items() if v}
    if "text" not in mapping or mapping["text"] not in df.columns:
        raise ValueError("A text column must be mapped.")
    for f, col in mapping.items():
        if f not in FIELDS:
            raise ValueError(f"Unknown field '{f}'.")
        if col not in df.columns:
            raise ValueError(f"Mapped column '{col}' for '{f}' is not in the file.")

    n_in = len(df)
    col = lambda f: df[mapping[f]].astype(str).str.strip() if f in mapping else pd.Series([""] * n_in, index=df.index)  # noqa: E731
    work = pd.DataFrame({"text": col("text"), "external_id": col("external_id"), "product": col("product"),
                         "channel": col("channel"), "cat_raw": col("category"), "sent_raw": col("sentiment")})
    missing = {f: int((col(f) == "").sum()) for f in mapping}
    warnings: list[str] = []
    if "date" in mapping:
        work["day"] = pd.to_datetime(col("date"), errors="coerce", format="mixed").dt.date
    else:
        work["day"] = date.today()
        warnings.append("No date column mapped: all complaints were dated with today's date, so time-series "
                        "analytics (trends, anomalies, forecasts) will not be meaningful for this file.")

    skipped = {"empty_text": int((work["text"] == "").sum()), "invalid_date": int(work["day"].isna().sum())}
    valid = work[(work["text"] != "") & work["day"].notna()].copy()
    valid["hash"] = valid["text"].map(text_hash)
    dup_in_file = int(valid.duplicated(["hash", "day"]).sum())
    valid = valid.drop_duplicates(["hash", "day"])
    existing = {(h, d) for h, d in db.execute(select(Complaint.text_hash, Complaint.created_at)
                                              .where(Complaint.text_hash.in_(valid["hash"].tolist()))).all()}
    mask = [(h, d) in existing for h, d in zip(valid["hash"], valid["day"])]
    dup_in_db = int(sum(mask))
    valid = valid[[not m for m in mask]]

    cats = valid["cat_raw"].map(_norm_category)
    unmapped = sorted({r for r, (_, bad) in zip(valid["cat_raw"], cats) if bad})
    valid["true_category"] = [c for c, _ in cats]
    valid["true_sentiment"] = valid["sent_raw"].str.lower().map(SENT_MAP)
    bad_sent = int(((valid["sent_raw"] != "") & valid["true_sentiment"].isna()).sum())
    if unmapped:
        warnings.append(f"{len(unmapped)} unknown category value(s) were mapped to 'Other': {', '.join(unmapped[:8])}")
    if bad_sent:
        warnings.append(f"{bad_sent} sentiment value(s) were not recognised and ignored.")

    job = ImportJob(filename=filename, mapping=mapping, status="completed")
    db.add(job)
    db.flush()
    recs = [{
        "external_id": (r.external_id or None), "text": r.text, "text_hash": r.hash, "created_at": r.day,
        "product": r.product or None, "channel": r.channel or None,
        "true_category": r.true_category if isinstance(r.true_category, str) else None,
        "true_sentiment": r.true_sentiment if isinstance(r.true_sentiment, str) else None,
        "is_synthetic": synthetic, "import_job_id": job.id} for r in valid.itertuples()]
    ids: list[int] = []
    for i in range(0, len(recs), 2000):
        objs = [Complaint(**r) for r in recs[i:i + 2000]]
        db.add_all(objs)
        db.flush()
        ids += [o.id for o in objs]
    job.summary = {"rows_in_file": n_in, "rows_imported": len(recs), "skipped": {**skipped, "duplicate_in_file": dup_in_file,
                                                                                   "duplicate_in_database": dup_in_db},
                   "missing_values": missing, "labeled_category": int(valid["true_category"].notna().sum()),
                   "labeled_sentiment": int(valid["true_sentiment"].notna().sum()), "warnings": warnings,
                   "date_range": [str(valid["day"].min()), str(valid["day"].max())] if len(valid) else None}
    db.commit()
    return job, ids


def seed_synthetic(db: Session, n_rows: int, seed: int = 42) -> tuple[ImportJob, list[int]]:
    db.execute(delete(Complaint).where(Complaint.is_synthetic.is_(True)))
    db.commit()
    df = datagen.generate(n_rows=n_rows, seed=seed)
    df["created_at"] = df["created_at"].astype(str)
    mapping = {"text": "text", "date": "created_at", "category": "true_category", "sentiment": "true_sentiment",
               "product": "product", "channel": "channel", "external_id": "external_id"}
    return import_dataframe(db, df, mapping, f"synthetic_seed{seed}_{n_rows}.csv", synthetic=True)


def dataset_stats(db: Session) -> dict:
    total = db.scalar(select(func.count(Complaint.id))) or 0
    synth = db.scalar(select(func.count(Complaint.id)).where(Complaint.is_synthetic.is_(True))) or 0
    lo, hi = db.execute(select(func.min(Complaint.created_at), func.max(Complaint.created_at))).one()
    return {"total": total, "synthetic": synth, "imported": total - synth,
            "labeled_category": db.scalar(select(func.count(Complaint.id)).where(Complaint.true_category.is_not(None))) or 0,
            "labeled_sentiment": db.scalar(select(func.count(Complaint.id)).where(Complaint.true_sentiment.is_not(None))) or 0,
            "date_min": lo, "date_max": hi,
            "is_fully_synthetic": total > 0 and synth == total}
