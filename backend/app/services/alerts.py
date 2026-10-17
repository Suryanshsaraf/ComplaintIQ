"""Rule-based alert generation on top of the ML outputs. Alerts are upserted by `dedup_key` so user-set
statuses (investigating / acknowledged / resolved) survive every refresh, retrain or re-import."""
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Alert
from . import timeseries as ts

SENT_WINDOW = 10        # recent days compared with ...
SENT_BASELINE = 28      # ... the 28 days before them
VOLUME_RECENCY = 14     # only episodes ending within this many days of the latest data create alerts


def _sev_from_z(z: float) -> str:
    return "critical" if z >= 8 else "high" if z >= 5 else "medium" if z >= 3.5 else "low"


def _upsert(db: Session, a: dict) -> str:
    row = db.scalar(select(Alert).where(Alert.dedup_key == a["dedup_key"]))
    if row is None:
        db.add(Alert(**a))
        return "created"
    if row.status != "resolved":  # never touch status; refresh numbers while still relevant
        for k in ("severity", "title", "explanation", "metrics", "baseline", "categories", "detected_for"):
            setattr(row, k, a[k])
    return "updated"


def build_candidates(df: pd.DataFrame, an: dict, fc: dict, em: dict, as_of: date) -> list[dict]:
    out: list[dict] = []
    wk = f"{as_of.isocalendar()[0]}-W{as_of.isocalendar()[1]:02d}"

    # 1. volume spikes (episodes of consecutive anomalous days)
    for ep in ts.episodes(an.get("anomalies", [])):
        if (as_of - ep["end"]).days > VOLUME_RECENCY:
            continue
        m = ep["metrics"]
        scope = ep["scope"]
        observed = m.get("volume_3d", m.get("volume"))
        expected = m.get("expected_3d", m.get("expected"))
        label = "3-day complaint volume" if "volume_3d" in m else "daily complaint volume"
        out.append({
            "dedup_key": f"volume_spike:{scope}:{ep['start']}", "type": "volume_spike",
            "severity": _sev_from_z(ep["peak_z"]),
            "title": f"{'Overall' if scope == 'All' else scope} complaint spike ({ep['start']:%b %d} - {ep['end']:%b %d})",
            "explanation": f"{label.capitalize()} reached {observed} against ~{expected} expected from the trailing "
                           f"28-day robust baseline (peak z={ep['peak_z']:.1f}, threshold {ts.Z_THRESHOLD}). "
                           f"{ep['days']} consecutive anomalous day(s). This flags a statistical deviation; "
                           f"it does not establish the cause.",
            "metrics": {"observed": observed, "peak_z": round(ep["peak_z"], 2), "days": ep["days"]},
            "baseline": {"expected": expected, "window_days": 28, "method": "rolling median / MAD"},
            "categories": [] if scope == "All" else [scope], "detected_for": ep["end"]})

    # 2. rising negative sentiment (one-sided two-proportion z-test, recent window vs. preceding baseline)
    d = df.copy()
    d["day"] = pd.to_datetime(d["day"]).dt.date
    r0 = as_of - timedelta(days=SENT_WINDOW - 1)
    b0 = r0 - timedelta(days=SENT_BASELINE)
    rec, base = d[(d["day"] >= r0)], d[(d["day"] >= b0) & (d["day"] < r0)]
    scopes = [("All", rec, base)] + [(c, rec[rec["category"] == c], base[base["category"] == c])
                                     for c in sorted(d["category"].unique())]
    for scope, r, b in scopes:
        if len(r) < 15 or len(b) < 30:
            continue
        pr, pb = (r["sentiment"] == "negative").mean(), (b["sentiment"] == "negative").mean()
        se = np.sqrt(pb * (1 - pb) / len(r)) or 1e-9
        z = (pr - pb) / max(se, 1e-9)
        if z >= 3.0 and pr - pb >= 0.10:
            out.append({
                "dedup_key": f"sentiment_decline:{scope}:{wk}", "type": "sentiment_decline",
                "severity": "high" if z >= 4.5 else "medium",
                "title": f"Negative sentiment rising{'' if scope == 'All' else ' in ' + scope}",
                "explanation": f"{pr:.0%} of the last {SENT_WINDOW} days' complaints ({len(r)}) are negative vs "
                               f"{pb:.0%} over the prior {SENT_BASELINE} days ({len(b)}); one-sided z={z:.1f}. "
                               f"Sentiment is model-predicted, and tests across categories are not multiplicity-corrected.",
                "metrics": {"negative_rate": round(float(pr), 3), "n": int(len(r)), "z": round(float(z), 2)},
                "baseline": {"negative_rate": round(float(pb), 3), "n": int(len(b)), "window_days": SENT_BASELINE},
                "categories": [] if scope == "All" else [scope], "detected_for": as_of})

    # 3. emerging topics / terms
    for iss in (em.get("issues") or [])[:5]:
        terms = ", ".join(f"“{t['term']}”" for t in iss["terms"][:4])
        out.append({
            "dedup_key": f"emerging_topic:{iss['category']}:{wk}", "type": "emerging_topic",
            "severity": "high" if iss["peak_ratio"] >= 10 else "medium",
            "title": f"Emerging issue in {iss['category']}: {iss['terms'][0]['term']}",
            "explanation": f"Terms {terms} appear in far more complaints during the last {em['recent_window_days']} "
                           f"days than in the preceding {em['baseline_window_days']}-day baseline "
                           f"(up to {iss['peak_ratio']:.0f}x relative document frequency).",
            "metrics": {"terms": iss["terms"][:6], "peak_ratio": round(iss["peak_ratio"], 1)},
            "baseline": {"window_days": em["baseline_window_days"], "n_docs": em["n_baseline"]},
            "categories": [iss["category"]], "detected_for": as_of})

    # 4. unusually high forecast
    if fc.get("status") == "ok":
        hist = np.array([h["n"] for h in fc["history"]][-28:], dtype=float)
        nxt = np.array([f["yhat"] for f in fc["forecast"][:7]])
        ratio = nxt.mean() / hist.mean() if hist.mean() > 0 else 0
        if ratio >= 1.25:
            out.append({
                "dedup_key": f"forecast_high:{wk}", "type": "forecast_high",
                "severity": "high" if ratio >= 1.5 else "medium",
                "title": "Forecast: complaint volume expected to stay elevated",
                "explanation": f"{fc['selected_model']} forecasts {nxt.mean():.0f}/day over the next 7 days, "
                               f"{ratio:.2f}x the last-28-day average ({hist.mean():.0f}/day). Forecasts extrapolate "
                               f"recent patterns, including any current incident.",
                "metrics": {"forecast_daily_avg_7d": round(float(nxt.mean()), 1), "ratio": round(float(ratio), 2)},
                "baseline": {"daily_avg_28d": round(float(hist.mean()), 1)},
                "categories": [], "detected_for": as_of})
    return out


def refresh_alerts(db: Session, df: pd.DataFrame, an: dict, fc: dict, em: dict, as_of: date) -> dict:
    res = {"created": 0, "updated": 0}
    for cand in build_candidates(df, an, fc, em, as_of):
        res[_upsert(db, cand)] += 1
    db.commit()
    return res


VALID_STATUS = ("open", "investigating", "acknowledged", "resolved")


def set_status(db: Session, alert: Alert, status: str, note: str | None = None) -> Alert:
    alert.notes = [*(alert.notes or []), {"at": datetime.utcnow().isoformat(timespec="seconds"),
                                          "from": alert.status, "to": status, "note": note or ""}]
    alert.status = status
    alert.updated_at = datetime.utcnow()
    db.commit()
    return alert
