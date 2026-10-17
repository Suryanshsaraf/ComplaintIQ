import json


def test_health_and_dashboard(client):
    h = client.get("/api/health").json()
    assert h["status"] == "ok" and h["models_ready"] and h["complaints"] > 3000
    s = client.get("/api/dashboard/summary?days=30").json()
    assert s["empty"] is False and s["kpis"]["total"]["value"] > 0
    assert s["data"]["is_fully_synthetic"] is True
    assert s["categories"] and s["topics"] and s["forecast"]["status"] == "ok"
    t = client.get("/api/dashboard/trends?days=60").json()
    assert len(t["series"]) > 30 and t["by_category"]


def test_complaint_search_filter_sort_pagination_export(client):
    r = client.get("/api/complaints?page=1&page_size=10&category=Delivery&sort=date&order=asc").json()
    assert len(r["items"]) == 10 and r["total"] > 10
    assert all(i["prediction"]["category"] == "Delivery" for i in r["items"])
    dates = [i["created_at"] for i in r["items"]]
    assert dates == sorted(dates)
    q = client.get("/api/complaints?q=refund&sentiment=negative").json()
    assert all("refund" in i["text"].lower() for i in q["items"])
    assert client.get("/api/complaints?sort=bogus").status_code == 422
    cid = r["items"][0]["id"]
    d = client.get(f"/api/complaints/{cid}").json()
    assert d["explanation"]["category_terms"] is not None and d["true_category"]    # truth kept separate
    assert client.get("/api/complaints/99999999").status_code == 404
    csv = client.get("/api/complaints/export?category=Delivery")
    assert csv.headers["content-type"].startswith("text/csv")
    assert csv.text.splitlines()[0].startswith("id,external_id") and len(csv.text.splitlines()) > 50


def test_predict_and_intelligence_endpoints(client):
    p = client.post("/api/predict", json={"text": "I was charged twice on my invoice and I am furious"}).json()
    assert p["category"] == "Billing" and p["sentiment"] == "negative"
    assert abs(sum(p["category_probabilities"].values()) - 1) < 1e-3
    assert client.post("/api/predict", json={"text": "x"}).status_code == 422
    ev = client.get("/api/nlp/evaluation?task=category").json()
    assert ev["status"] == "ok" and any(m["is_selected"] for m in ev["models"])
    assert client.get("/api/nlp/evaluation?task=sentiment").json()["models"]
    assert client.get("/api/nlp/topics").json()["topics"][0]["representatives"]
    assert client.get("/api/nlp/keywords").json()["keywords"]
    cl = client.get("/api/ml/clusters").json()
    assert cl["k"] >= 6 and cl["points"]
    an = client.get("/api/ml/anomalies?days=365").json()
    assert an["status"] == "ok" and an["anomalies"]
    assert len(client.get("/api/ml/forecast?horizon=7").json()["forecast"]) == 7
    assert client.get("/api/ml/forecast?horizon=9").status_code == 422


def test_known_injected_incidents_are_detected(client):
    an = client.get("/api/ml/anomalies?days=365&method=rolling_zscore").json()["anomalies"]
    assert any(a["category"] == "Billing" and "2026-03-29" <= a["day"] <= "2026-04-06" for a in an)
    assert any(a["category"] == "Delivery" and "2026-07-09" <= a["day"] <= "2026-07-20" for a in an)
    assert any(a["category"] == "Delivery" and a["day"] >= "2026-10-10" for a in an)
    types = {a["type"] for a in client.get("/api/alerts").json()}
    assert {"volume_spike", "emerging_topic"} <= types


def test_alert_status_persists_across_refresh(client):
    alerts = client.get("/api/alerts?status=active").json()
    assert len(alerts) >= 2
    aid, bid = alerts[0]["id"], alerts[1]["id"]
    r = client.patch(f"/api/alerts/{aid}", json={"status": "acknowledged", "note": "looking"})
    assert r.status_code == 200 and r.json()["status"] == "acknowledged"
    client.patch(f"/api/alerts/{bid}", json={"status": "resolved"})
    client.post("/api/alerts/refresh")                       # recompute everything
    assert client.get(f"/api/alerts/{aid}").json()["status"] == "acknowledged"
    assert client.get(f"/api/alerts/{bid}").json()["status"] == "resolved"
    assert client.get(f"/api/alerts/{aid}").json()["notes"][0]["note"] == "looking"
    from app.db import SessionLocal           # fresh session, as after a restart
    from app.models import Alert
    with SessionLocal() as db:
        assert db.get(Alert, aid).status == "acknowledged"
    assert client.patch(f"/api/alerts/{aid}", json={"status": "nonsense"}).status_code == 422
    assert client.patch("/api/alerts/999999", json={"status": "open"}).status_code == 404


CSV = """Ticket,Message,Received,Dept,Bad
1,My parcel never arrived and tracking is stuck,2026-10-14,Delivery,x
2,Charged twice on my invoice,2026-10-15,Billing,x
2,Charged twice on my invoice,2026-10-15,Billing,x
3,,2026-10-15,Billing,x
4,Wi-Fi keeps dropping on my router,not-a-date,Technical Support,x
5,The agent was rude to me,2026-10-15,Weird Dept,x
"""


def test_csv_import_mapping_validation_and_unlabeled(client):
    raw = CSV.encode()
    pv = client.post("/api/imports/preview", files={"file": ("t.csv", raw, "text/csv")}).json()
    assert pv["n_rows"] == 6 and pv["suggested_mapping"]["text"] == "Message"
    assert pv["blank_counts"]["Message"] == 1
    before = client.get("/api/datasets/stats").json()["total"]
    mapping = {"text": "Message", "date": "Received", "category": "Dept", "external_id": "Ticket"}
    r = client.post("/api/imports", files={"file": ("t.csv", raw, "text/csv")}, data={"mapping": json.dumps(mapping)}).json()
    s = r["summary"]
    assert s["rows_imported"] == 3 and s["skipped"]["empty_text"] == 1 and s["skipped"]["invalid_date"] == 1
    assert s["skipped"]["duplicate_in_file"] == 1 and any("Weird Dept" in w for w in s["warnings"])
    assert client.get("/api/datasets/stats").json()["total"] == before + 3
    again = client.post("/api/imports", files={"file": ("t.csv", raw, "text/csv")}, data={"mapping": json.dumps(mapping)}).json()
    assert again["summary"]["rows_imported"] == 0 and again["summary"]["skipped"]["duplicate_in_database"] == 3
    # unlabeled upload: scored by the stored models, ground truth stays empty
    un = b"msg,when\nMy refund still has not arrived after three weeks,2026-10-15\n"
    r2 = client.post("/api/imports", files={"file": ("u.csv", un, "text/csv")},
                     data={"mapping": json.dumps({"text": "msg", "date": "when"})}).json()
    assert r2["scored"] == 1
    hit = client.get("/api/complaints?q=refund still has not arrived").json()["items"][0]
    assert hit["true_category"] is None and hit["prediction"]["category"] == "Refunds"
    # error handling
    assert client.post("/api/imports", files={"file": ("t.csv", raw, "text/csv")}, data={"mapping": "{}"}).status_code == 422
    assert client.post("/api/imports/preview", files={"file": ("e.csv", b"", "text/csv")}).status_code == 422
    assert client.post("/api/imports", files={"file": ("t.csv", raw, "text/csv")}, data={"mapping": "nope"}).status_code == 422
