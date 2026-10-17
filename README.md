# ComplaintIQ — Customer Complaint Intelligence & Early-Warning System

ComplaintIQ ingests customer complaints, classifies them, discovers recurring topics, flags unusual spikes, forecasts
complaint volume and raises alerts that analysts can investigate, acknowledge and resolve. It combines **NLP**
(TF-IDF + linear classifiers, NMF topics, keyword extraction) with **advanced ML techniques** (KMeans clustering,
Isolation Forest and robust-statistics anomaly detection, Holt-Winters / seasonal forecasting) behind a FastAPI
backend and a React dashboard. It runs fully locally — no paid APIs, no external LLMs, no dataset downloads.

> **All bundled data is synthetic.** It is template-generated with controlled incident spikes and is flagged
> `is_synthetic` in the database and in the UI. Metrics on it show that the pipeline works; they are **not** a
> claim about real-world accuracy (templated text is far easier than real complaints).

## Abstract

Complaint teams drown in free text. ComplaintIQ turns it into (1) labels — category and sentiment predicted by
leakage-controlled linear models, (2) structure — NMF topics and KMeans clusters with representative complaints,
(3) early warnings — rolling robust z-scores and an Isolation Forest on daily volume / sentiment features, plus
surging-term detection, and (4) foresight — a chronologically validated 7/14/30-day volume forecast with prediction
intervals. Rule-based alert generation sits on top, and alert lifecycle state is persisted in the database.

## Architecture

```mermaid
flowchart LR
  subgraph Browser
    UI["React + TS + Tailwind<br/>Recharts / Lucide<br/>5 pages"]
  end
  subgraph Backend["FastAPI (backend/app)"]
    R["routers/<br/>dashboard · complaints · intelligence · alerts · datasets"]
    S["services/<br/>nlp · classifiers · unsupervised<br/>timeseries · alerts · datasets · pipeline"]
    A[("artifacts/*.joblib<br/>trained models")]
  end
  DB[("SQLite (dev) / PostgreSQL<br/>SQLAlchemy")]
  UI -- "REST /api (JSON, CSV)" --> R --> S
  S <--> A
  S <--> DB
  R <--> DB
```

Dashboards only **read stored results**; models are trained at bootstrap or on an explicit *Retrain* action,
never per request. Imports score new rows with the stored models and recompute the cheap time-series analytics.

## ML pipeline

```mermaid
flowchart TD
  D["complaints (synthetic or CSV import)"] --> C["clean_text / tokenizer<br/>negations kept, bigrams"]
  C --> SUP["Supervised (labelled rows)<br/>stratified 80/20 split<br/>TF-IDF inside Pipeline<br/>LogReg · Calibrated LinearSVM · majority baseline<br/>5-fold CV on train → pick model<br/>report on test"]
  C --> UNS["Unsupervised (all rows)<br/>NMF topics · TF-IDF keywords<br/>TF-IDF → SVD → KMeans (k by silhouette)"]
  SUP --> P["predictions table<br/>category, probability, sentiment, topic, cluster, keywords"]
  UNS --> P
  P --> TS["daily series (as-of = latest complaint date)"]
  TS --> AN["anomalies: weekday-adjusted rolling median/MAD z-score<br/>(overall, per-category 3-day, 7-day negative rate)<br/>+ Isolation Forest"]
  TS --> FC["forecast: seasonal naive vs seasonal mean vs Holt-Winters<br/>28-day chronological holdout, MAE/RMSE, 80% interval"]
  P --> EM["emerging terms: recent 14d vs prior 60d document frequency"]
  AN --> AL["alert rules → alerts table (upsert by dedup_key)"]
  FC --> AL
  EM --> AL
  P --> AL
```

## Database

```mermaid
erDiagram
  import_jobs ||--o{ complaints : imported
  complaints ||--o| predictions : "1:1 model output"
  model_runs ||--o{ evaluation_results : has
  import_jobs { int id string filename json mapping json summary }
  complaints { int id string text date created_at string product string channel string true_category string true_sentiment bool is_synthetic }
  predictions { int complaint_id string category float category_prob string sentiment float sentiment_score int topic_id int cluster_id json keywords string split }
  model_runs { int id string kind string name json result bool is_active }
  evaluation_results { int id string task string model_name float accuracy float f1_macro json confusion }
  anomalies { int id date day string method float score json triggers string explanation }
  alerts { int id string dedup_key string type string severity string status json notes json metrics json baseline }
```

Ground truth (`complaints.true_*`) and model output (`predictions.*`) are separate tables, so labels are never
overwritten and unlabeled uploads work. `predictions.split` records whether a row was in the `train` or `test`
split (or `external` = never used for fitting).

## NLP algorithms

* **Preprocessing** (`services/nlp.py`): lower-casing, contraction expansion, URL/e-mail/digit removal,
  custom stop-word list that **keeps negations** (`not`, `no`, `never`, `without`, …), uni+bigrams so “not working”
  stays distinct from “working”. No NLTK corpus downloads are needed.
* **Sentiment** (negative/neutral/positive) and **category** (Billing, Delivery, Product Quality, Technical Support,
  Refunds, Account Issues, Customer Service, Other): TF-IDF → Logistic Regression and Calibrated Linear SVM, plus a
  majority-class baseline. Sentiment score = P(positive) − P(negative).
* **Topics**: NMF on TF-IDF (k = 8). **Keywords**: per-document top TF-IDF terms/phrases (unigrams covered by a
  chosen bigram are dropped); global keywords by mean TF-IDF.
* **Explanations**: for a complaint, tf-idf × coefficient of the predicted class gives the terms that pushed the
  model there. This describes the model, **not** real-world causes. The UI says so.

## ATML algorithms

* **Clustering**: TF-IDF → TruncatedSVD(100) → L2 normalise → KMeans; k ∈ 6..12 chosen by silhouette on a sample.
  Cluster size, top centroid terms, representative complaints (closest to centroid), sentiment/category mix, and a
  2-D PCA scatter. Agreement with known categories (ARI/NMI) is reported *only as an external check*.
* **Anomaly detection** (explainable):
  * *Rolling statistical baseline*: weekday-adjusted counts vs the trailing 28-day median/MAD (floored by a Poisson
    scale) for overall daily volume; per-category **3-day** sums (small daily counts are too noisy); and a 7-day
    negative-sentiment rate with a binomial-aware scale. Threshold z ≥ 3.5.
  * *Isolation Forest* on [adjusted volume, negative rate, avg sentiment, change vs prior week …]; each flagged day
    lists the features that are > 2 robust σ from typical and the category with the largest excess.
* **Forecasting**: seasonal naive (baseline), seasonal mean (4 weeks), damped-trend additive Holt-Winters with weekly
  seasonality. All fitted on data before a 28-day chronological hold-out; MAE/RMSE/bias reported; lowest RMSE is
  refit on all history. Intervals: 80%, simulated for Holt-Winters, hold-out-RMSE band otherwise. Fewer than 56 days
  of history → a graceful “insufficient data” response.
* **Alerts** (`services/alerts.py`): volume-spike episodes, rising negative sentiment (one-sided two-proportion
  z-test, last 10 vs prior 28 days), emerging topics (terms ≥ 3× more frequent in the last 14 days vs the prior 60,
  ≥ 12 recent docs), high forecast (next-7-day mean ≥ 1.25× last-28-day mean). Alerts are upserted by a dedup key, so
  refreshes never reset the status you set.

## Dataset

`services/datagen.py` creates ~7,000 complaints (seed 42) over 365 days ending 2026-10-15 with weekday seasonality, a
mild upward trend, products, channels, and noise (10% cross-category sentences, 10% mismatched sentiment closers,
30% of texts without a sentiment closer). Injected incidents (ground truth in `spike_definitions()`):

| Incident | Window | Effect |
|---|---|---|
| Billing double-charge | 2026-03-29 → 04-03 | ×3.2 Billing volume, more negative |
| Delivery incident | 2026-07-12 → 07-17 | ×3.5 Delivery volume |
| Recent delivery surge | 2026-10-10 → 10-15 | ×3.2 Delivery, “carrier backlog” vocabulary |
| App 5.2 update bug | 2026-09-28 → 10-15 | ×1.9 Technical Support, new vocabulary (“token expired”, “login loop”) |
| Service sentiment drop | 2026-10-06 → 10-15 | Customer Service ×1.8 volume, +30 pts negative |

Time-based analytics use the **latest complaint date in the data** as “now”, so the demo is reproducible.
`backend/data/sample_complaints.csv` (labelled) and `sample_unlabeled.csv` (500 unlabeled rows, different seed and
column names) are included for import demos.

### CSV import

Upload → preview (columns, first rows, per-column blank counts, suggested mapping) → configurable mapping of
text / date / category / sentiment / product / channel / id → validation and summary: empty text and invalid dates are
skipped, duplicates (same normalised text + date) are skipped within the file and against the database, unknown
category values map to “Other” with a warning, missing values are counted per column. Without a date column, rows are
dated today and a warning explains trends will not be meaningful. Unlabeled rows are scored by the stored models;
labelled rows are used at the next *Retrain*.

## Evaluation results (actual run on the bundled synthetic data)

Stratified 80/20 split, 1,392 test complaints, TF-IDF fitted on training data only, model chosen by 5-fold CV macro-F1
on the training split. **Synthetic, template-based text — treat as a pipeline sanity check.**

| Task | Model | Accuracy | Macro P | Macro R | Macro F1 | CV F1 | ECE |
|---|---|---|---|---|---|---|---|
| Category | Majority baseline | 19.8% | 2.5% | 12.5% | 4.1% | 4.1% | – |
| Category | Logistic Regression | 97.8% | 97.5% | 97.9% | 97.7% | 97.3% | 0.034 |
| Category | **Linear SVM (calibrated, deployed)** | 98.1% | 98.1% | 98.0% | 98.1% | 97.7% | 0.011 |
| Sentiment | Majority baseline | 66.9% | 22.3% | 33.3% | 26.7% | 26.7% | – |
| Sentiment | Logistic Regression | 79.3% | 70.0% | 76.2% | 72.5% | 71.1% | 0.039 |
| Sentiment | **Linear SVM (calibrated, deployed)** | 86.0% | 84.8% | 76.2% | 79.7% | 78.0% | 0.028 |

Sentiment is harder by construction (30% of texts have no sentiment cue and 10% of cues are deliberately mismatched).
Confusion matrices and per-class precision/recall/F1 are in *NLP Intelligence → Classification*.

| Component | Result |
|---|---|
| Clustering | k = 12, silhouette 0.074 (low — short templated text), ARI 0.42 / NMI 0.58 vs known categories |
| Forecast (28-day hold-out) | Seasonal naive MAE 6.64 / RMSE 8.89; **Seasonal mean (selected)** 6.11 / 8.03 (−9.7% RMSE); Holt-Winters 6.30 / 8.42 |
| Anomalies | 20 days flagged by the statistical method, 11 by Isolation Forest, 1 by both |
| Alerts at bootstrap | 3 volume spikes, 1 sentiment decline, 2 emerging topics |

Controlled-spike tests confirm the Billing incident, the July Delivery incident and the October Delivery surge are
detected by the statistical method, and the delivery/app-update vocabulary surfaces as emerging issues. Some other
days are flagged by chance (e.g. a Billing flag on 2026-03-13, “Other” on 2026-09-16/17) — thresholds trade false alarms
against sensitivity. Isolation Forest flags a fixed 3% of days by design and agrees with the statistical method on few
of them.

## Installation

Requirements: Python 3.10+, Node 18+.

```bash
# backend
cd backend
python -m venv .venv && .venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# frontend
cd ../frontend
npm install
```

Optional: copy `.env.example` to `.env` (repo root) to change the database URL, synthetic row count or CORS origins.
For PostgreSQL set `DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/complaintiq` and `pip install psycopg2-binary`
(schema uses only portable SQLAlchemy types; the alert/trend queries have a PostgreSQL branch but were **only tested on SQLite**).

## Quick Start (Single Command)

```bash
# On macOS / Linux:
./run.sh

# On Windows:
run.bat
```
This automatically verifies/installs dependencies, bootstraps the database and models, and starts both backend (`:8000`) and frontend (`:5173`).

## Manual Run

```bash
# terminal 1 — API on :8000 (first start seeds ~7,000 synthetic complaints and trains models, ~40 s)
cd backend
python -m uvicorn app.main:app --port 8000

# terminal 2 — UI on :5173 (proxies /api to :8000)
cd frontend
npm run dev
```

Open http://localhost:5173 (API docs: http://localhost:8000/docs).

### Training / data commands

```bash
cd backend
python -m app.cli bootstrap              # seed synthetic data (if DB empty) + train + analytics
python -m app.cli train                  # retrain on everything in the DB
python -m app.cli sample-data            # (re)write backend/data/sample_*.csv
```
The UI also has **Retrain models** (NLP / ML pages), **Re-run detection** (Alert Center) and the API has
`DELETE /api/datasets/synthetic` / `POST /api/datasets/synthetic` to remove or regenerate the demo data. To start over,
delete `backend/data/complaintiq.db` and `backend/artifacts/*.joblib`.

### Tests

```bash
cd backend && python -m pytest -q          # 16 tests: NLP, classification, clustering, anomalies (controlled
                                           # spikes), forecasting, CSV import, alert persistence, API
cd frontend && npm test && npm run build   # 8 vitest tests, type-check + production build
```

## API summary (full schema at `/docs`)

| Area | Endpoints |
|---|---|
| System | `GET /api/health` |
| Dashboard | `GET /api/dashboard/summary?days=`, `GET /api/dashboard/trends?days=&granularity=day\|week` |
| Complaints | `GET /api/complaints` (q, date_from/to, category, sentiment, channel, product, topic_id, cluster_id, page, page_size, sort, order), `GET /api/complaints/{id}`, `GET /api/complaints/export` (same filters, CSV), `GET /api/complaints/filter-options`, `POST /api/predict` |
| Datasets | `POST /api/imports/preview`, `POST /api/imports`, `GET /api/imports`, `GET /api/datasets/stats`, `DELETE/POST /api/datasets/synthetic` |
| NLP | `GET /api/nlp/sentiment`, `/api/nlp/evaluation?task=category\|sentiment`, `/api/nlp/topics`, `/api/nlp/keywords?category=` |
| ML | `GET /api/ml/clusters`, `/api/ml/anomalies?days=&method=`, `/api/ml/forecast?horizon=7\|14\|30`, `/api/ml/emerging`, `GET /api/models/runs`, `POST /api/models/retrain` |
| Alerts | `GET /api/alerts?status=&severity=&type=`, `GET /api/alerts/counts`, `GET/PATCH /api/alerts/{id}` (`status`, `note`), `POST /api/alerts/refresh` |

## Project layout

```
backend/app/{main,config,db,models,schemas,cli}.py
backend/app/routers/     dashboard, complaints, intelligence, alerts, datasets
backend/app/services/    nlp, datagen, classifiers, unsupervised, timeseries, alerts, datasets, pipeline
backend/tests/           pytest suite        backend/data/  sample CSVs (+ SQLite DB at runtime)
backend/artifacts/       trained *.joblib (created on first run)
frontend/src/pages/      Overview, Explorer, NLPIntelligence, MLIntelligence, AlertCenter
frontend/src/components/ shadcn/ui-style primitives (ui.tsx), charts.tsx
```

## Known limitations

* Bundled data is synthetic and templated; real complaints will give lower accuracy, noisier topics and clusters.
  The model-selection/evaluation code is generic, but no real dataset was evaluated here.
* Predicted-class probabilities come from a calibrated linear SVM / LR; ECE is reported on the test split but
  they can still be over-confident on real or out-of-distribution text (many demo predictions show ~100%).
* The sentiment model is trained on the synthetic labels; on uploaded real text it is a weak, domain-shifted baseline.
  Uploading labelled data and retraining adapts it.
* Statistical anomaly thresholds produce occasional chance flags; per-category tests are not multiplicity-corrected.
  Alerts report deviations, not causes. Alerts are never auto-resolved when conditions subside.
* Forecasts are for total daily volume only (no per-category forecasts); the hold-out window contains recent
  incidents, which inflates every model's error.
* Imports score rows with existing models and refresh time-series analytics; topics/clusters are not refit until
  *Retrain*. Training and retraining are synchronous HTTP calls (≈30–40 s on the demo data).
* Uploaded data is mixed with whatever is already in the database (including synthetic rows) — delete the synthetic
  data via `DELETE /api/datasets/synthetic` for a clean analysis.
* No authentication; intended for local use. PostgreSQL support is untested.
* Frontend is unit-tested only at the utility/component level; page flows were verified manually and via headless
  screenshots, not with an end-to-end browser test suite.
