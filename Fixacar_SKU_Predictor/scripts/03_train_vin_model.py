#!/usr/bin/env python3
"""
03_train_vin_model.py

Purpose:
- Train VIN prediction models using pure-Python + SQLite/joblib (no NumPy/sklearn)
- Predict targets: maker, model, series (as categorical labels)
- Save encoders and model weights into models/vin/

Approach (baseline):
- Simple frequency-based priors + KNN-like nearest lookup on (wmi, vds)
- For minimal dataset, this is robust; for larger datasets, we can extend to
  logistic regression or Naive Bayes implemented in NumPy.
"""
from pathlib import Path
import time
import joblib
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models" / "vin"
MODELS.mkdir(parents=True, exist_ok=True)
DB_PATH = ROOT / "Source_Files" / "processed_consolidado.db"


def load_vin_training_from_db():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT vin_number, maker, model, series
            FROM processed_consolidado
            WHERE vin_number IS NOT NULL AND LENGTH(vin_number)=17
                  AND maker IS NOT NULL AND model IS NOT NULL AND series IS NOT NULL
            """
        )
        rows = cur.fetchall()
        vins = []
        for vin, maker, model, series in rows:
            wmi = (vin or "")[:3]
            vds = (vin or "")[3:6]
            vins.append((wmi, vds, str(maker), str(model), str(series)))
        return vins
    finally:
        conn.close()


def build_label_encoders(vins):
    encoders = {}
    makers = sorted({m for _,_,m,_,_ in vins})
    models = sorted({y for _,_,_,y,_ in vins})
    series = sorted({s for _,_,_,_,s in vins})
    encoders["maker"] = {lab:i for i,lab in enumerate(makers)}
    encoders["model"] = {lab:i for i,lab in enumerate(models)}
    encoders["series"] = {lab:i for i,lab in enumerate(series)}
    return encoders


def encode_feature_keys_from_vins(vins) -> dict:
    from collections import defaultdict, Counter
    freq = defaultdict(lambda: {"maker": Counter(), "model": Counter(), "series": Counter()})
    for wmi, vds, maker, model, series in vins:
        key = (wmi or "", vds or "")
        freq[key]["maker"][maker] += 1
        freq[key]["model"][model] += 1
        freq[key]["series"][series] += 1
    lookup = {}
    for key, counters in freq.items():
        lookup[key] = {
            "maker": counters["maker"].most_common(1)[0][0] if counters["maker"] else "UNKNOWN",
            "model": counters["model"].most_common(1)[0][0] if counters["model"] else "UNKNOWN",
            "series": counters["series"].most_common(1)[0][0] if counters["series"] else "UNKNOWN",
        }
    return lookup


def train_and_save():
    t0 = time.time()
    vins = load_vin_training_from_db()

    # Build encoders and lookup from VIN tuples
    encoders = build_label_encoders(vins)
    lookup = encode_feature_keys_from_vins(vins)

    # Save artifacts
    joblib.dump(encoders, MODELS / "encoders.joblib")
    joblib.dump(lookup, MODELS / "lookup_model.joblib")

    # Save metadata
    meta = {
        "version": 1,
        "algorithm": "nearest-key(mode)",
        "features": ["wmi", "vds"],
        "n_rows": len(vins),
        "n_keys": len(lookup),
        "elapsed_s": round(time.time() - t0, 3),
    }
    import json
    with open(MODELS / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("[OK] VIN models trained and saved in:", MODELS)


def main():
    train_and_save()


if __name__ == "__main__":
    main()

