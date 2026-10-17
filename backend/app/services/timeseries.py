"""Time-series analytics: anomaly detection, volume forecasting, emerging-term detection.

All functions are pure (DataFrame in, dict out) so they can be unit-tested on controlled data.
Input frames use columns: day (datetime.date), category, sentiment, score, plus id/text where noted.
"""
import warnings
from datetime import date, timedelta

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import CountVectorizer

from .nlp import analyzer_unigram_bigram
from .unsupervised import dedupe_phrases

Z_THRESHOLD = 3.5
MIN_FORECAST_DAYS = 56


# ---------------------------------------------------------------- helpers
def daily_frame(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["day"] = pd.to_datetime(d["day"])
    d["neg"] = (d["sentiment"] == "negative").astype(int)
    g = d.groupby("day").agg(n=("neg", "size"), neg=("neg", "sum"), avg_sent=("score", "mean"))
    g = g.reindex(pd.date_range(g.index.min(), g.index.max(), freq="D"))
    g["n"] = g["n"].fillna(0)
    g["neg"] = g["neg"].fillna(0)
    g["neg_rate"] = (g["neg"] / g["n"]).where(g["n"] >= 3)
    return g


def category_daily(df: pd.DataFrame, index: pd.DatetimeIndex) -> pd.DataFrame:
    d = df.copy()
    d["day"] = pd.to_datetime(d["day"])
    return d.pivot_table(index="day", columns="category", values="sentiment", aggfunc="size").reindex(index).fillna(0)


def _robust(s: pd.Series, window: int, shift: int):
    prior = s.shift(shift)
    base = prior.rolling(window, min_periods=window // 2).median()
    mad = prior.rolling(window, min_periods=window // 2).apply(lambda x: np.median(np.abs(x - np.median(x))), raw=True)
    return base, 1.4826 * mad


def _weekday_factors(n: pd.Series) -> np.ndarray:
    f = n.groupby(n.index.weekday).mean().reindex(range(7)).fillna(n.mean()).values
    return f / f.mean() if f.mean() > 0 else np.ones(7)


# ---------------------------------------------------------------- anomalies
def detect_anomalies(df: pd.DataFrame, contamination: float = 0.03, z_threshold: float = Z_THRESHOLD) -> dict:
    if df.empty or df["day"].nunique() < 35:
        return {"status": "insufficient_data", "anomalies": [], "daily": [], "summary": {}}
    g = daily_frame(df)
    cats = category_daily(df, g.index)
    f = _weekday_factors(g["n"])[g.index.weekday]
    adj = g["n"] / f
    out: list[dict] = []

    # --- overall daily volume (rolling robust z-score on weekday-adjusted counts)
    base, sc = _robust(adj, 28, 1)
    scale = np.maximum(sc, np.sqrt(np.maximum(base, 1)))
    z_vol = (adj - base) / scale
    cat_base = cats.shift(1).rolling(28, min_periods=14).median()
    excess = cats - cat_base

    def top_cat(day):
        if day not in excess.index:
            return None, 0.0
        row = excess.loc[day].dropna()
        if row.empty or row.max() < 2:
            return None, 0.0
        return str(row.idxmax()), float(row.max())

    for day in g.index[(z_vol >= z_threshold) & (adj >= 1.3 * base)]:
        cat, ex = top_cat(day)
        expected = float(base[day] * f[g.index.get_loc(day)])
        out.append({"day": day.date(), "method": "rolling_zscore", "category": cat, "score": float(z_vol[day]),
                    "triggers": ["volume"],
                    "metrics": {"scope": "All", "volume": int(g.loc[day, "n"]), "expected": round(expected, 1),
                                "z": round(float(z_vol[day]), 2)},
                    "explanation": f"Volume {int(g.loc[day, 'n'])} vs ~{expected:.0f} expected for this weekday "
                                   f"(robust z={z_vol[day]:.1f}, threshold {z_threshold})."
                                   + (f" Largest excess in {cat} (+{ex:.0f})." if cat else "")})

    # --- per-category 3-day volume (small counts are noisy, so a 3-day sum is monitored)
    cat_series_z = {}
    for c in cats.columns:
        s3 = (cats[c] / f).rolling(3).sum()
        b3, sc3 = _robust(s3, 28, 3)
        z3 = (s3 - b3) / (1.3 * np.sqrt(np.maximum(b3, 1)))  # Poisson scale + dispersion allowance
        cat_series_z[c] = z3
        flag = (z3 >= z_threshold) & (s3 >= 1.8 * b3) & (s3 >= 8)
        for day in g.index[flag]:
            actual = int(cats[c].loc[day - timedelta(days=2): day].sum())
            expected = float(b3[day])
            out.append({"day": day.date(), "method": "rolling_zscore", "category": str(c), "score": float(z3[day]),
                        "triggers": ["category_volume"],
                        "metrics": {"scope": str(c), "volume_3d": actual, "expected_3d": round(expected, 1),
                                    "z": round(float(z3[day]), 2)},
                        "explanation": f"{c}: {actual} complaints in the last 3 days vs ~{expected:.0f} expected "
                                       f"(robust z={z3[day]:.1f})."})

    # --- overall negative-sentiment rate (7-day trailing, binomial-aware scale)
    n7, neg7 = g["n"].rolling(7).sum(), g["neg"].rolling(7).sum()
    nr7 = neg7 / n7.where(n7 > 0)
    bs, ss = _robust(nr7, 28, 7)
    scale_s = np.maximum(ss, np.sqrt(np.maximum(bs * (1 - bs), 0.01) / n7.clip(lower=1)))
    z_sent = (nr7 - bs) / scale_s
    for day in g.index[(z_sent >= z_threshold) & (nr7 - bs >= 0.05)]:
        cat, _ = top_cat(day)
        out.append({"day": day.date(), "method": "rolling_zscore", "category": cat, "score": float(z_sent[day]),
                    "triggers": ["negative_rate"],
                    "metrics": {"scope": "All", "negative_rate_7d": round(float(nr7[day]), 3),
                                "baseline": round(float(bs[day]), 3), "z": round(float(z_sent[day]), 2)},
                    "explanation": f"7-day negative-sentiment rate {nr7[day]:.0%} vs {bs[day]:.0%} baseline "
                                   f"(z={z_sent[day]:.1f})."})

    # --- Isolation Forest on multivariate daily features
    feat = pd.DataFrame({
        "volume": adj,
        "negative_rate": g["neg_rate"].fillna(g["neg_rate"].median()),
        "avg_sentiment": g["avg_sent"].fillna(g["avg_sent"].median()),
        "volume_vs_prior_week": adj - adj.shift(1).rolling(7).mean(),
        "neg_rate_vs_prior_week": g["neg_rate"].fillna(g["neg_rate"].median())
        - g["neg_rate"].fillna(g["neg_rate"].median()).shift(1).rolling(7).mean(),
    }).dropna()
    if len(feat) >= 30:
        iso = IsolationForest(n_estimators=300, contamination=contamination, random_state=0).fit(feat.values)
        pred, sc_iso = iso.predict(feat.values), -iso.score_samples(feat.values)
        med, mad = feat.median(), (feat - feat.median()).abs().median() * 1.4826 + 1e-9
        for i, day in enumerate(feat.index):
            if pred[i] != -1:
                continue
            zf = ((feat.iloc[i] - med) / mad)
            trig = [k for k, v in zf.items() if abs(v) >= 2.0]
            desc = "; ".join(f"{k.replace('_', ' ')} {'high' if zf[k] > 0 else 'low'} ({zf[k]:+.1f}σ)"
                             for k in sorted(trig, key=lambda k: -abs(zf[k]))[:3]) or "multivariate combination unusual"
            cat, ex = top_cat(day)
            out.append({"day": day.date(), "method": "isolation_forest", "category": cat, "score": float(sc_iso[i]),
                        "triggers": trig,
                        "metrics": {"volume_adj": round(float(feat.iloc[i]["volume"]), 1),
                                    "negative_rate": round(float(feat.iloc[i]["negative_rate"]), 3),
                                    "avg_sentiment": round(float(feat.iloc[i]["avg_sentiment"]), 3),
                                    "feature_z": {k: round(float(v), 2) for k, v in zf.items()}},
                        "explanation": f"Isolation Forest isolated this day quickly: {desc}."
                                       + (f" Largest category excess: {cat} (+{ex:.0f})." if cat else "")})

    stat_days = {a["day"] for a in out if a["method"] == "rolling_zscore"}
    iso_days = {a["day"] for a in out if a["method"] == "isolation_forest"}
    daily = [{"day": d.date().isoformat(), "n": int(r.n), "baseline": None if np.isnan(base[d]) else round(float(base[d] * f[i]), 1),
              "upper": None if np.isnan(base[d]) else round(float((base[d] + z_threshold * scale[d]) * f[i]), 1),
              "neg_rate": None if np.isnan(r.neg_rate) else round(float(r.neg_rate), 3),
              "stat_flag": d.date() in stat_days, "iso_flag": d.date() in iso_days}
             for i, (d, r) in enumerate(g.iterrows())]
    return {"status": "ok", "anomalies": sorted(out, key=lambda a: (a["day"], a["method"])), "daily": daily,
            "summary": {"statistical_days": len(stat_days), "isolation_forest_days": len(iso_days),
                        "both_methods": len(stat_days & iso_days), "z_threshold": z_threshold,
                        "contamination": contamination, "days_analysed": len(g)},
            "category_z": {c: z.fillna(0).round(2).tolist()[-30:] for c, z in cat_series_z.items()}}


def episodes(anoms: list[dict], key=lambda a: a["category"], gap: int = 1) -> list[dict]:
    """Group consecutive-day statistical anomalies of the same scope into episodes."""
    by: dict = {}
    for a in anoms:
        if a["method"] != "rolling_zscore" or a["triggers"] not in (["volume"], ["category_volume"]):
            continue
        by.setdefault(a["metrics"].get("scope", "All"), []).append(a)
    res = []
    for scope, items in by.items():
        items.sort(key=lambda a: a["day"])
        cur = [items[0]]
        for a in items[1:]:
            if (a["day"] - cur[-1]["day"]).days <= gap + 1:
                cur.append(a)
            else:
                res.append((scope, cur)); cur = [a]
        res.append((scope, cur))
    return [{"scope": s, "start": c[0]["day"], "end": c[-1]["day"], "peak_z": max(a["score"] for a in c),
             "days": len(c), "metrics": max(c, key=lambda a: a["score"])["metrics"]} for s, c in res]


# ---------------------------------------------------------------- forecasting
def _seasonal_naive(train: np.ndarray, h: int) -> np.ndarray:
    return np.array([train[-7 + (i % 7)] for i in range(h)], dtype=float)


def _seasonal_mean(train: np.ndarray, h: int, weeks: int = 4) -> np.ndarray:
    w = min(weeks, len(train) // 7)
    mat = np.array([train[len(train) - 7 * (k + 1): len(train) - 7 * k] for k in range(w)])
    prof = mat.mean(0)
    return np.array([prof[i % 7] for i in range(h)])


def _holt_winters(train: np.ndarray, h: int, simulate: bool = False):
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = ExponentialSmoothing(train.astype(float) + 1.0, trend="add", damped_trend=True, seasonal="add",
                                   seasonal_periods=7, initialization_method="estimated").fit()
        mean = fit.forecast(h) - 1.0
        sims = None
        if simulate:
            try:
                sims = fit.simulate(h, repetitions=500, error="add", anchor="end", random_state=0) - 1.0
                sims = np.asarray(sims)
            except Exception:  # pragma: no cover - statsmodels version differences
                sims = None
    return np.maximum(np.asarray(mean), 0), sims


MODELS = {"Seasonal naive (last week)": lambda tr, h: _seasonal_naive(tr, h),
          "Seasonal mean (4 weeks)": lambda tr, h: _seasonal_mean(tr, h),
          "Holt-Winters (damped, weekly)": lambda tr, h: _holt_winters(tr, h)[0]}


def forecast_volume(df: pd.DataFrame, horizon: int = 30, holdout: int = 28) -> dict:
    if df.empty:
        return {"status": "insufficient_data", "reason": "No complaints available.", "min_days": MIN_FORECAST_DAYS}
    g = daily_frame(df)
    y = g["n"].values.astype(float)
    if len(y) < MIN_FORECAST_DAYS:
        return {"status": "insufficient_data", "available_days": int(len(y)), "min_days": MIN_FORECAST_DAYS,
                "reason": f"Need at least {MIN_FORECAST_DAYS} days of history to evaluate a weekly-seasonal forecast; "
                          f"only {len(y)} available."}
    train, test = y[:-holdout], y[-holdout:]
    evals, preds = [], {}
    for name, fn in MODELS.items():
        try:
            p = np.asarray(fn(train, holdout), dtype=float)
        except Exception as exc:  # model failed to fit -> report, don't crash
            evals.append({"model": name, "error": str(exc)}); continue
        preds[name] = p
        err = test - p
        evals.append({"model": name, "mae": float(np.abs(err).mean()), "rmse": float(np.sqrt((err ** 2).mean())),
                      "bias": float(err.mean())})
    ok = [e for e in evals if "rmse" in e]
    best = min(ok, key=lambda e: e["rmse"])["model"]
    baseline = "Seasonal naive (last week)"
    for e in ok:
        e["is_baseline"] = e["model"] == baseline
        e["is_selected"] = e["model"] == best
    rmse_best = next(e["rmse"] for e in ok if e["model"] == best)

    # refit on all history and forecast with 80% interval
    lo = hi = None
    if best.startswith("Holt"):
        mean, sims = _holt_winters(y, horizon, simulate=True)
        if sims is not None:
            lo, hi = np.maximum(np.percentile(sims, 10, axis=1), 0), np.percentile(sims, 90, axis=1)
    else:
        mean = MODELS[best](y, horizon)
    if lo is None:  # fall back to a holdout-RMSE band
        band = 1.2816 * rmse_best
        lo, hi = np.maximum(mean - band, 0), mean + band
    last = g.index[-1]
    fdays = [(last + timedelta(days=i + 1)).date().isoformat() for i in range(horizon)]
    hold_days = [d.date().isoformat() for d in g.index[-holdout:]]
    return {
        "status": "ok", "selected_model": best, "baseline_model": baseline, "evaluation": evals,
        "holdout_days": holdout, "interval": "80% (simulated)" if best.startswith("Holt") and sims is not None
        else "80% (holdout RMSE band)",
        "history": [{"day": d.date().isoformat(), "n": int(v)} for d, v in zip(g.index[-120:], y[-120:])],
        "holdout": [{"day": d, "actual": float(a), **{m: round(float(preds[m][i]), 2) for m in preds}}
                    for i, (d, a) in enumerate(zip(hold_days, test))],
        "forecast": [{"day": d, "yhat": round(float(m), 2), "lower": round(float(l), 2), "upper": round(float(u), 2)}
                     for d, m, l, u in zip(fdays, mean, lo, hi)],
        "improvement_vs_baseline_rmse": float(1 - rmse_best / next(e["rmse"] for e in ok if e["model"] == baseline))
        if any(e["model"] == baseline for e in ok) else None,
        "caveat": "Chronological hold-out on the last 28 days; recent incident spikes in the hold-out inflate "
                  "every model's error. Forecasts assume current patterns persist.",
    }


# ---------------------------------------------------------------- emerging terms
def emerging_terms(df: pd.DataFrame, as_of: date, recent_days: int = 14, base_days: int = 60,
                   min_recent: int = 12, min_ratio: float = 3.0) -> dict:
    d = df.copy()
    d["day"] = pd.to_datetime(d["day"]).dt.date
    r_start = as_of - timedelta(days=recent_days - 1)
    b_start = r_start - timedelta(days=base_days)
    rec = d[(d["day"] >= r_start) & (d["day"] <= as_of)].reset_index(drop=True)
    base = d[(d["day"] >= b_start) & (d["day"] < r_start)].reset_index(drop=True)
    res = {"as_of": as_of.isoformat(), "recent_window_days": recent_days, "baseline_window_days": base_days,
           "n_recent": int(len(rec)), "n_baseline": int(len(base)), "issues": []}
    if len(rec) < 30 or len(base) < 60:
        res["status"] = "insufficient_data"
        return res
    cv = CountVectorizer(analyzer=analyzer_unigram_bigram, binary=True, min_df=3)
    cv.fit(pd.concat([rec["text"], base["text"]]))
    Xr, Xb = cv.transform(rec["text"]).tocsc(), cv.transform(base["text"])
    names = cv.get_feature_names_out()
    r = np.asarray(Xr.sum(0)).ravel()
    b = np.asarray(Xb.sum(0)).ravel()
    ratio = ((r + 0.5) / len(rec)) / ((b + 0.5) / len(base))
    cand = np.where((r >= min_recent) & (ratio >= min_ratio))[0]
    cand = cand[np.argsort(-(ratio[cand] * np.log1p(r[cand])))][:40]
    groups: dict[str, list[int]] = {}
    for j in cand:
        rows = Xr[:, j].nonzero()[0]
        cat = rec.loc[rows, "category"].value_counts().idxmax()
        groups.setdefault(cat, []).append(j)
    for cat, cols in groups.items():
        keep = dedupe_phrases([names[j] for j in cols], 6)
        cols = [j for j in cols if names[j] in keep]
        score = np.asarray(Xr[:, cols].sum(1)).ravel()
        ex_idx = np.argsort(-score)[:3]
        res["issues"].append({
            "category": cat, "n_terms": len(cols), "peak_ratio": float(ratio[cols].max()),
            "terms": [{"term": str(names[j]), "recent_docs": int(r[j]), "baseline_docs": int(b[j]),
                       "ratio": round(float(ratio[j]), 1)} for j in cols],
            "examples": [{"id": int(rec.loc[i, "id"]), "text": rec.loc[i, "text"]} for i in ex_idx if score[i] > 0]})
    res["issues"].sort(key=lambda x: -x["peak_ratio"] * x["n_terms"])
    res["status"] = "ok"
    return res
