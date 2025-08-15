#!/usr/bin/env python3
"""
04_train_sku_model.py

Purpose:
- Train SKU frequency lookup model using pure-Python + SQLite/joblib (no NumPy)
- Save model weights and metadata under models/sku/

Baseline model:
- Regularized linear regression (ridge-like) via closed-form solution
  theta = (X^T X + λI)^-1 X^T y
- Features: price + simple encodings from brand/sku (hashed embeddings)
"""
from pathlib import Path
import json
import time
import joblib
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models" / "sku"
MODELS.mkdir(parents=True, exist_ok=True)
DB_PATH = ROOT / "Source_Files" / "processed_consolidado.db"


def load_sku_aggregates_from_db():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT maker, series, descripcion, normalized_descripcion, referencia,
                   start_year, end_year, frequency, global_sku_frequency
            FROM sku_year_ranges
            WHERE referencia IS NOT NULL
            """
        )
        return cur.fetchall()
    finally:
        conn.close()


def hash_feature(col: list[str], dim: int = 16):
    # Simple hashing trick to encode categorical variables
    # Returns list[list[float]] for portability (no NumPy dependency)
    n = len(col)
    out = [[0.0 for _ in range(dim)] for _ in range(n)]
    for i, val in enumerate(col):
        s = (val or "").lower()
        h = abs(hash(s))
        idx = h % dim
        out[i][idx] = 1.0
    return out


def build_frequency_lookup(rows):
    # Build a lookup keyed by (maker, series, year, description_match_type) -> list of (referencia, freq, start,end,global)
    from collections import defaultdict
    exact = defaultdict(list)
    normalized = defaultdict(list)
    for maker, series, descripcion, normalized_desc, referencia, start_year, end_year, freq, global_freq in rows:
        # store under each year in range for fast lookup by exact year
        for year in range(int(start_year), int(end_year)+1):
            exact[(maker.lower(), series.lower(), year, descripcion.lower())].append((referencia, freq, start_year, end_year, global_freq))
            normalized[(maker.lower(), series.lower(), year, normalized_desc.lower())].append((referencia, freq, start_year, end_year, global_freq))

    # Sort lists by frequency desc
    for d in (exact, normalized):
        for k, lst in d.items():
            lst.sort(key=lambda x: (-int(x[1]), -int(x[4]), x[0]))
    return {"exact": dict(exact), "normalized": dict(normalized)}




def train_and_save():
    t0 = time.time()
    rows = load_sku_aggregates_from_db()
    lookup = build_frequency_lookup(rows)

    joblib.dump(lookup, MODELS / "sku_frequency_lookup.joblib")

    meta = {
        "version": 1,
        "algorithm": "sku_year_range_frequency",
        "n_rows": len(rows),
        "n_keys_exact": len(lookup["exact"]),
        "n_keys_normalized": len(lookup["normalized"]),
        "elapsed_s": round(time.time() - t0, 3),
    }
    with open(MODELS / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("[OK] SKU frequency model saved in:", MODELS)


def main():
    train_and_save()


if __name__ == "__main__":
    main()

