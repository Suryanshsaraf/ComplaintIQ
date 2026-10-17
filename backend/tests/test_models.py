from datetime import date, timedelta

import numpy as np
import pandas as pd

from app.services import classifiers as clf
from app.services import datagen
from app.services import timeseries as ts
from app.services import unsupervised as uns


def _df(n=3000):
    return datagen.generate(n_rows=n, seed=7)


def test_category_classifier_beats_baseline_without_leakage():
    df = _df()
    out = clf.train_classifier(df["text"].tolist(), df["true_category"].tolist())
    assert out is not None
    assert not (out["is_train"] & out["is_test"]).any()          # disjoint splits
    res = {r["model_name"]: r for r in out["results"]}
    assert res["Linear SVM"]["accuracy"] > 0.9 and res["Logistic Regression"]["f1_macro"] > 0.9
    assert res["Majority baseline"]["accuracy"] < 0.3
    sel = next(r for r in out["results"] if r["is_selected"])
    assert sel["model_name"] != "Majority baseline"
    assert np.array(sel["confusion"]).sum() == sel["n_test"]
    assert 0 <= sel["ece"] <= 1


def test_sentiment_classifier_runs_and_explains():
    df = _df()
    out = clf.train_classifier(df["text"].tolist(), df["true_sentiment"].tolist())
    sel = next(r for r in out["results"] if r["is_selected"])
    assert sel["accuracy"] > 0.7
    terms = clf.explain(out["pipeline"], "I am extremely frustrated and not happy", "negative")
    assert terms and all(t["weight"] > 0 for t in terms)


def test_classifier_declines_tiny_data():
    assert clf.train_classifier(["a b c"] * 10, ["x"] * 10) is None


def test_clustering_recovers_structure_and_topics():
    df = _df()
    kv = uns.make_keyword_vec()
    X = kv.fit_transform(df["text"])
    cl = uns.fit_clusters(df["text"].tolist(), X, kv.get_feature_names_out())
    assert 6 <= cl["k"] <= 12 and len(cl["points"]) > 100
    ev = uns.cluster_vs_labels(cl["labels"], df["true_category"].tolist())
    assert ev["nmi"] > 0.3
    tp = uns.fit_topics(df["text"].tolist())
    assert len(tp["topics"]) == 8 and all(t["terms"] for t in tp["topics"])


def _frame(counts, start=date(2026, 1, 1), cat="Delivery", neg=0.6, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for i, n in enumerate(counts):
        for _ in range(int(n)):
            rows.append((start + timedelta(days=i), cat, "negative" if rng.random() < neg else "neutral", -0.5))
    return pd.DataFrame(rows, columns=["day", "category", "sentiment", "score"])


def test_anomaly_detection_flags_controlled_spike_and_not_flat_noise():
    rng = np.random.default_rng(1)
    base = rng.poisson(20, 120).astype(float)
    flat = ts.detect_anomalies(_frame(base))
    flat_days = {a["day"] for a in flat["anomalies"] if a["method"] == "rolling_zscore" and "volume" in a["triggers"]}
    assert len(flat_days) <= 1
    spiked = base.copy()
    spiked[90:93] *= 4                                            # injected spike
    res = ts.detect_anomalies(_frame(spiked))
    spike_days = {date(2026, 1, 1) + timedelta(days=i) for i in (90, 91, 92)}
    assert {a["day"] for a in res["anomalies"] if a["method"] == "rolling_zscore"} & spike_days
    assert {a["day"] for a in res["anomalies"] if a["method"] == "isolation_forest"} & spike_days
    assert all(a["explanation"] for a in res["anomalies"])


def test_anomaly_detection_handles_short_series():
    assert ts.detect_anomalies(_frame([5] * 10))["status"] == "insufficient_data"


def test_forecast_chronological_holdout_and_insufficient_data():
    rng = np.random.default_rng(3)
    t = np.arange(140)
    y = rng.poisson(30 + 8 * np.sin(2 * np.pi * t / 7) + 0.05 * t)
    out = ts.forecast_volume(_frame(y), horizon=30)
    assert out["status"] == "ok" and len(out["forecast"]) == 30
    ev = {e["model"]: e for e in out["evaluation"]}
    assert ev["Seasonal naive (last week)"]["is_baseline"]
    assert min(e["rmse"] for e in ev.values()) <= ev["Seasonal naive (last week)"]["rmse"]
    assert all(f["lower"] <= f["yhat"] <= f["upper"] + 1e-6 for f in out["forecast"])
    assert ts.forecast_volume(_frame(y[:30]))["status"] == "insufficient_data"
    empty = pd.DataFrame(columns=["day", "category", "sentiment", "score"])
    assert ts.forecast_volume(empty)["status"] == "insufficient_data"
