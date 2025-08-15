#!/usr/bin/env python3
"""
02_process_data_polars.py

Purpose:
- Load consolidado.json from Source_Files/
- Perform basic cleaning/feature engineering with Polars
- Save processed tables into:
  - data/processed/*.parquet
  - Source_Files/processed_consolidado.db (SQLite) for convenience

No pandas/sklearn dependencies. Universal on x64/ARM64.
"""
from pathlib import Path
import json
import sqlite3
from datetime import datetime
import time
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Source_Files"
DATA = ROOT / "data" / "processed"
DATA.mkdir(parents=True, exist_ok=True)
DB_PATH = SRC / "processed_consolidado.db"
ITEMS_PARQUET = DATA / "items_flat.parquet"
# Ensure directories exist
SRC.mkdir(parents=True, exist_ok=True)



# Load raw records (with nested 'items') from consolidado.json
# Returns list[dict]
def load_consolidado_records_raw():
    path = SRC / "consolidado.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if isinstance(raw, list):
        records = raw
    elif isinstance(raw, dict):
        for key in ("records", "data", "items", "rows"):
            if key in raw and isinstance(raw[key], list):
                records = raw[key]
                break
        else:
            raise ValueError("consolidado.json: expected list at top-level or a 'records'/'data'/'items'/'rows' list in object")
    else:
        raise ValueError("consolidado.json: unsupported JSON structure")

    if not records:
        raise ValueError("consolidado.json appears to be empty")
    if not all(isinstance(x, dict) for x in records):
        raise ValueError("consolidado.json: expected list of objects (dicts)")

    return records


def load_consolidado() -> pl.DataFrame:
    path = SRC / "consolidado.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Accept either a list of records or an object with one of several keys
    if isinstance(raw, list):
        records = raw
    elif isinstance(raw, dict):
        for key in ("records", "data", "items", "rows"):
            if key in raw and isinstance(raw[key], list):
                records = raw[key]
                break
        else:
            raise ValueError("consolidado.json: expected list at top-level or a 'records'/'data'/'items'/'rows' list in object")
    else:
        raise ValueError("consolidado.json: unsupported JSON structure")

    if not records:
        raise ValueError("consolidado.json appears to be empty")

    # Ensure each item is a mapping
    if not all(isinstance(x, dict) for x in records):
        raise ValueError("consolidado.json: expected list of objects (dicts)")

    # Project only needed fields and coerce types to avoid mixed-type errors
    def to_str(v):
        if v is None:
            return None
        return str(v)

    def to_float(v):
        if v is None:
            return None
        try:
            if isinstance(v, str):
                v = v.replace(",", "").strip()
                if v == "":
                    return None
            return float(v)
        except Exception:
            return None

    projected = []
    for r in records:
        projected.append({
            "vin": to_str(r.get("vin", "")),
            "sku": to_str(r.get("sku", "")),
            "brand": to_str(r.get("brand", "")),
            "maker": to_str(r.get("maker", "")),
            "model": to_str(r.get("model", "")),
            "series": to_str(r.get("series", "")),
            "price": to_float(r.get("price")),
        })

    return pl.DataFrame(projected, strict=False)


def feature_engineer(df: pl.DataFrame) -> pl.DataFrame:
    # Ensure required columns exist; if absent, create as nulls
    for col in ("vin", "sku", "brand", "price"):
        if col not in df.columns:
            df = df.with_columns(pl.lit(None).alias(col))

    # Example transforms: normalize text fields, basic encodings
    df = df.with_columns([
        pl.col("vin").cast(pl.Utf8).str.to_uppercase(),
        pl.col("sku").cast(pl.Utf8).str.to_uppercase(),
        pl.col("brand").cast(pl.Utf8).str.strip_chars(),
        pl.col("price").cast(pl.Float64),
    ])
    # Extract VIN-derived features (very simple placeholder)
    df = df.with_columns([
        (pl.col("vin").str.slice(0, 3)).alias("wmi"),
        (pl.col("vin").str.slice(3, 6)).alias("vds"),
    ])
    # Basic numeric safety
    df = df.with_columns([
        pl.when(pl.col("price").is_nan() | pl.col("price").is_null())
          .then(0.0)
          .otherwise(pl.col("price"))
          .alias("price")
    ])
    return df


def write_parquet(df: pl.DataFrame):
    df.write_parquet(DATA / "consolidado_processed.parquet")


# Use the unified text processor for consistent normalization across Step 2 and Step 5
try:
    import sys as _sys
    _sys.path.append(str((ROOT / "portable_app" / "src").resolve()))
    from utils.unified_text import unified_text_preprocessing as normalize_text_basic
except Exception:
    def normalize_text_basic(s: str) -> str:
        # Last resort fallback (should rarely be used)
        return (str(s).lower().strip() if s is not None else "")



def build_sku_year_ranges(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    # Drop and recreate table
    cur.execute("DROP TABLE IF EXISTS sku_year_ranges")
    cur.execute(
        """
        CREATE TABLE sku_year_ranges (
            maker TEXT,
            series TEXT,
            descripcion TEXT,
            normalized_descripcion TEXT,
            referencia TEXT,
            start_year INTEGER,
            end_year INTEGER,
            frequency INTEGER,
            global_sku_frequency INTEGER,
            PRIMARY KEY (maker, series, descripcion, referencia)
        )
        """
    )

    # Aggregate base stats
    # Enforce year bounds in aggregation as well
    _min_year = 1990
    _max_year = datetime.now().year + 2
    cur.execute(
        f"""
        WITH base AS (
            SELECT maker, series, descripcion, normalized_descripcion, referencia, model as year, COUNT(*) AS freq
            FROM processed_consolidado
            WHERE referencia IS NOT NULL AND TRIM(COALESCE(referencia, '')) <> ''
              AND maker IS NOT NULL AND series IS NOT NULL AND model IS NOT NULL
              AND model BETWEEN {_min_year} AND {_max_year}
            GROUP BY maker, series, descripcion, normalized_descripcion, referencia, model
        ),
        global_freq AS (
            SELECT referencia, SUM(freq) AS gfreq FROM base GROUP BY referencia
        )
        SELECT b.maker, b.series, b.descripcion, b.normalized_descripcion, b.referencia,
               MIN(b.year) AS start_year, MAX(b.year) AS end_year, SUM(b.freq) AS frequency,
               gf.gfreq AS global_sku_frequency
        FROM base b
        JOIN global_freq gf ON gf.referencia = b.referencia
        GROUP BY b.maker, b.series, b.descripcion, b.normalized_descripcion, b.referencia
        """
    )
    rows = cur.fetchall()
    cur.executemany(
        """
        INSERT OR REPLACE INTO sku_year_ranges
        (maker, series, descripcion, normalized_descripcion, referencia, start_year, end_year, frequency, global_sku_frequency)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )
    # Indexes for performance
    cur.execute('CREATE INDEX IF NOT EXISTS idx_sku_year_range_lookup ON sku_year_ranges (maker, series, start_year, end_year)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_sku_frequency ON sku_year_ranges (frequency DESC)')
    conn.commit()
    return len(rows)


def build_vin_prefix_frequencies(conn: sqlite3.Connection) -> int:
    """Create table with VIN prefix (first 11 chars masked) frequencies per maker/model/series.
    Discards suspicious VINs using a robust validator.
    Frequency counts distinct VINs to avoid multiplying by items per vehicle.
    """
    # Register VIN validator as SQLite UDF
    import re

    def _is_valid_vin(vin: str) -> int:
        if not vin:
            return 0
        try:
            v = str(vin).strip().upper()
        except Exception:
            return 0
        # Length must be exactly 17
        if len(v) != 17:
            return 0
        # Allowed characters (no I, O, Q) and alphanumeric only
        if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", v):
            return 0
        # Must contain at least one letter and one digit
        if not (re.search(r"[A-Z]", v) and re.search(r"[0-9]", v)):
            return 0
        # No same character repeated 5 or more times consecutively
        if re.search(r"(.)\1{4,}", v):
            return 0
        # No more than 8 identical characters overall
        from collections import Counter as _Counter
        cnt = _Counter(v)
        if any(c >= 9 for c in cnt.values()):
            return 0
        # Disallow long obvious sequences (e.g., 123456 or ABCDEF in 6+ run)
        if re.search(r"012345|123456|234567|345678|456789", v):
            return 0
        if re.search(r"ABCDEF|BCDEFG|CDEFGH|DEFGHI|EFGHIJ|FGHIJK", v):
            return 0
        # Year code (pos 10, index 9) should be valid
        valid_year_codes = set("ABCDEFGHJKLMNPRSTUVWXYZ123456789")
        if v[9] not in valid_year_codes:
            return 0
        # Optional: Check digit algorithm (enable strict mode if needed)
        # def _check_digit_ok(vin):
        #     transl = {**{c:i for i,c in enumerate('0123456789')},
        #               **{c:v for c,v in zip('ABCDEFGHJKLMNPRSTUVWXYZ',[1,2,3,4,5,6,7,8,1,2,3,4,5,7,9,2,3,4,5,6,7,8,9])}}
        #     weights = [8,7,6,5,4,3,2,10,0,9,8,7,6,5,4,3,2]
        #     total = sum(transl[v[i]] * weights[i] for i in range(17))
        #     chk = 'X' if total % 11 == 10 else str(total % 11)
        #     return vin[8] == chk
        # if not _check_digit_ok(v):
        #     return 0
        return 1

    conn.create_function("is_valid_vin", 1, _is_valid_vin)

    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS vin_prefix_frequencies")
    cur.execute(
        """
        CREATE TABLE vin_prefix_frequencies (
            vin_mask TEXT,
            maker TEXT,
            model INTEGER,
            series TEXT,
            frequency INTEGER,
            PRIMARY KEY (vin_mask, maker, model, series)
        )
        """
    )
    cur.execute(
        """
        INSERT OR REPLACE INTO vin_prefix_frequencies (vin_mask, maker, model, series, frequency)
        SELECT SUBSTR(UPPER(vin_number), 1, 11) || 'XXXXXX' AS vin_mask,
               maker, model, series,
               COUNT(DISTINCT UPPER(vin_number)) AS frequency
        FROM processed_consolidado
        WHERE vin_number IS NOT NULL
          AND maker IS NOT NULL AND model IS NOT NULL AND series IS NOT NULL
          AND is_valid_vin(vin_number)
        GROUP BY vin_mask, maker, model, series
        """
    )
    # Helpful indexes
    cur.execute('CREATE INDEX IF NOT EXISTS idx_vin_mask_lookup ON vin_prefix_frequencies (vin_mask, maker, model, series)')
    conn.commit()
    # Return row count
    cur.execute('SELECT COUNT(*) FROM vin_prefix_frequencies')
    return cur.fetchone()[0]



def write_sqlite_processed(records: list[dict]) -> tuple[int, int]:
    """
    Create processed_consolidado.db with schema expected by the previous pipeline.
    Expands each record's items into rows.
    Returns: (inserted_rows, distinct_vins)
    """
    # Always replace the DB if it exists
    try:
        import os
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
    except Exception:
        pass

    conn = sqlite3.connect(DB_PATH)
    inserted = 0
    vins = set()
    try:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS processed_consolidado")
        cur.execute(
            """
            CREATE TABLE processed_consolidado (
                vin_number TEXT,
                maker TEXT,
                model INTEGER,
                series TEXT,
                descripcion TEXT,
                normalized_descripcion TEXT,
                referencia TEXT
            )
            """
        )
        rows = []
        for rec in records:
            # VIN normalization using shared function (I->1, O/Q->0, uppercase)
            from utils.unified_text import canonicalize_vin_chars, normalize_series as _normalize_series
            vin_raw = rec.get("vin_number") or rec.get("vin")
            vin = canonicalize_vin_chars(vin_raw) if vin_raw else None

            # maker/series lowercase; model as int; normalize series via Series tab
            maker_raw = rec.get("maker")
            maker = str(maker_raw).lower() if maker_raw is not None else None

            model = rec.get("model")
            try:
                # Enforce valid automotive model years: [1990, current_year+2]
                _min_year = 1990
                _max_year = datetime.now().year + 2
                if model is not None and str(model).isdigit():
                    _m = int(str(model))
                    model = _m if (_min_year <= _m <= _max_year) else None
                else:
                    model = None
            except Exception:
                model = None

            series_raw = rec.get("series")
            series = _normalize_series(maker, series_raw) if series_raw is not None else None
            series = str(series).lower() if series is not None else None

            items = rec.get("items") or rec.get("Items") or []
            if not isinstance(items, list):
                items = []
            if vin:
                vins.add(str(vin))
            if not items:
                # still insert a row with empty descripcion/referencia to preserve vehicle-level info
                rows.append((vin, maker, model, series, None, None, None))
                continue
            for it in items:
                desc_raw = it.get("descripcion") or it.get("description") or it.get("descripcion_general") or it.get("detalle")
                desc = str(desc_raw).lower() if desc_raw is not None else None
                ref = it.get("referencia") or it.get("reference") or it.get("ref")
                norm = normalize_text_basic(desc) if desc else None
                rows.append((vin, maker, model, series, desc, norm, ref))

        cur.executemany(
            "INSERT INTO processed_consolidado (vin_number, maker, model, series, descripcion, normalized_descripcion, referencia) VALUES (?,?,?,?,?,?,?)",
            rows,
        )
        inserted = len(rows)
        # Build sku_year_ranges after inserting base rows
        yr_count = build_sku_year_ranges(conn)
        vp_count = build_vin_prefix_frequencies(conn)
        conn.commit()
        return inserted, len(vins)
    finally:
        conn.close()


def main():
    t0 = time.time()
    print("[INFO] Processing consolidado with Polars...")
    df = load_consolidado()
    print(f"[INFO] Loaded {len(df)} records from consolidado.json")
    df = feature_engineer(df)

    write_parquet(df)
    # Build processed_consolidado.db compatible with prior stack
    raw_records = load_consolidado_records_raw()
    inserted, distinct_vins = write_sqlite_processed(raw_records)
    elapsed = time.time() - t0

    print("[OK] Processing complete:")
    print(f"   - Rows: {len(df)} | Columns: {len(df.columns)} | Took: {elapsed:.2f}s")

    print(f"   - Inserted into processed_consolidado: {inserted} rows | VINs: {distinct_vins}")
    print(f"   - Parquet: {DATA / 'consolidado_processed.parquet'}")
    print(f"   - SQLite: {DB_PATH}")


if __name__ == "__main__":
    main()

