"""Command line helpers:  python -m app.cli bootstrap | train | sample-data"""
import argparse
import json
from datetime import timedelta

from .config import DATA_DIR, SYNTHETIC_ROWS
from .db import SessionLocal, init_db
from .services import datagen, pipeline as pl


def main():
    ap = argparse.ArgumentParser(prog="app.cli")
    ap.add_argument("command", choices=["bootstrap", "train", "sample-data"])
    ap.add_argument("--rows", type=int, default=SYNTHETIC_ROWS)
    a = ap.parse_args()
    init_db()
    if a.command == "sample-data":
        df = datagen.generate(n_rows=a.rows)
        df.to_csv(DATA_DIR / "sample_complaints.csv", index=False)
        # a different seed => new texts, so importing this file is not rejected as duplicates of the seeded data
        un = datagen.generate(n_rows=a.rows, seed=99).drop(columns=["true_category", "true_sentiment"])
        un = un[un["created_at"] >= datagen.END_DATE - timedelta(days=45)].head(500)
        un["external_id"] = [f"UPL-{i + 1:05d}" for i in range(len(un))]
        un.rename(columns={"created_at": "date_received", "text": "complaint_text"}).to_csv(
            DATA_DIR / "sample_unlabeled.csv", index=False)
        print(f"wrote {len(df)} rows to {DATA_DIR}")
        return
    from .main import bootstrap
    with SessionLocal() as db:
        out = pl.train_all(db) if a.command == "train" else bootstrap(db, a.rows)
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
