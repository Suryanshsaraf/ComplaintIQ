"""ORM tables. Ground-truth labels (Complaint.true_*) are kept apart from model output (Prediction)."""
from datetime import date, datetime

from sqlalchemy import (JSON, Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _now():
    return datetime.utcnow()


class ImportJob(Base):
    __tablename__ = "import_jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="completed")
    mapping: Mapped[dict] = mapped_column(JSON, default=dict)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Complaint(Base):
    __tablename__ = "complaints"
    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    text_hash: Mapped[str] = mapped_column(String(40), index=True)
    created_at: Mapped[date] = mapped_column(Date, index=True)
    product: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    channel: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    # ground truth (optional, never overwritten by models)
    true_category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    true_sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
    import_job_id: Mapped[int | None] = mapped_column(ForeignKey("import_jobs.id", ondelete="SET NULL"),
                                                      nullable=True)
    prediction: Mapped["Prediction | None"] = relationship(back_populates="complaint", uselist=False,
                                                           cascade="all, delete-orphan")


class Prediction(Base):
    __tablename__ = "predictions"
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id", ondelete="CASCADE"), primary_key=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    category_prob: Mapped[float] = mapped_column(Float)
    sentiment: Mapped[str] = mapped_column(String(20), index=True)
    sentiment_score: Mapped[float] = mapped_column(Float)  # P(positive) - P(negative), in [-1, 1]
    topic_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cluster_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    split: Mapped[str] = mapped_column(String(12), default="unlabeled")  # train | test | unlabeled
    model_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    complaint: Mapped[Complaint] = relationship(back_populates="prediction")


class ModelRun(Base):
    __tablename__ = "model_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(30), index=True)  # category|sentiment|topics|clusters|anomalies|forecast
    name: Mapped[str] = mapped_column(String(80))
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    n_rows: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    model_run_id: Mapped[int] = mapped_column(ForeignKey("model_runs.id", ondelete="CASCADE"), index=True)
    task: Mapped[str] = mapped_column(String(30))
    model_name: Mapped[str] = mapped_column(String(60))
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    accuracy: Mapped[float] = mapped_column(Float)
    precision_macro: Mapped[float] = mapped_column(Float)
    recall_macro: Mapped[float] = mapped_column(Float)
    f1_macro: Mapped[float] = mapped_column(Float)
    cv_f1_macro: Mapped[float | None] = mapped_column(Float, nullable=True)
    labels: Mapped[list] = mapped_column(JSON, default=list)
    confusion: Mapped[list] = mapped_column(JSON, default=list)
    per_class: Mapped[dict] = mapped_column(JSON, default=dict)
    n_train: Mapped[int] = mapped_column(Integer, default=0)
    n_test: Mapped[int] = mapped_column(Integer, default=0)


class Anomaly(Base):
    __tablename__ = "anomalies"
    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    method: Mapped[str] = mapped_column(String(30))  # rolling_zscore | isolation_forest
    score: Mapped[float] = mapped_column(Float)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    triggers: Mapped[list] = mapped_column(JSON, default=list)
    explanation: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    model_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (UniqueConstraint("dedup_key", name="uq_alert_dedup"), Index("ix_alert_status", "status"))
    id: Mapped[int] = mapped_column(primary_key=True)
    dedup_key: Mapped[str] = mapped_column(String(120))
    type: Mapped[str] = mapped_column(String(30))  # volume_spike|sentiment_decline|emerging_topic|forecast_high
    severity: Mapped[str] = mapped_column(String(10))  # low|medium|high|critical
    title: Mapped[str] = mapped_column(String(200))
    explanation: Mapped[str] = mapped_column(Text)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    baseline: Mapped[dict] = mapped_column(JSON, default=dict)
    categories: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open|investigating|acknowledged|resolved
    notes: Mapped[list] = mapped_column(JSON, default=list)
    detected_for: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)
