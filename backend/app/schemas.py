from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class PredictionOut(BaseModel):
    category: str
    category_prob: float = Field(description="Model probability (see calibration/ECE in the evaluation page)")
    sentiment: str
    sentiment_score: float
    topic_id: int | None = None
    cluster_id: int | None = None
    keywords: list[str] = []
    split: str = Field(description="train | test | external: whether the row was used to fit the classifier")

    model_config = {"from_attributes": True}


class ComplaintOut(BaseModel):
    id: int
    external_id: str | None
    text: str
    created_at: date
    product: str | None
    channel: str | None
    true_category: str | None
    true_sentiment: str | None
    is_synthetic: bool
    prediction: PredictionOut | None

    model_config = {"from_attributes": True}


class ComplaintPage(BaseModel):
    items: list[ComplaintOut]
    total: int
    page: int
    page_size: int


class PredictIn(BaseModel):
    text: str = Field(min_length=3, max_length=5000)


class AlertOut(BaseModel):
    id: int
    type: str
    severity: str
    title: str
    explanation: str
    metrics: dict[str, Any]
    baseline: dict[str, Any]
    categories: list[str]
    status: str
    notes: list[dict[str, Any]]
    detected_for: date | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertPatch(BaseModel):
    status: Literal["open", "investigating", "acknowledged", "resolved"]
    note: str | None = Field(default=None, max_length=500)


class ImportRequestMeta(BaseModel):
    mapping: dict[str, str | None]
