#!/usr/bin/env python3
"""
Overnight validation script:
- Confirms processed_consolidado.db exists and has required tables
- Computes top 30 referencias by global_sku_frequency from sku_year_ranges
- For each referencia, picks a representative (maker, model, series, descripcion)
- Finds a real VIN with that (maker, model, series)
- Runs YearRangeDatabaseOptimizer predictions using original and normalized descriptions
- Verifies whether known referencia appears in predictions
- Analyzes nouns near direction adjectives to propose new Noun_Gender entries
- Writes a report to Fixacar_SKU_Predictor/logs/overnight_report.txt

This does not launch the GUI; it validates Step 5 backend logic deterministically.
"""
from __future__ import annotations
import os, sys, sqlite3, re, json
from collections import Counter, defaultdict
from pathlib import Path
from typing import List, Dict, Tuple

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'Source_Files'
LOGS = ROOT / 'logs'
LOGS.mkdir(parents=True, exist_ok=True)
DB_PATH = SRC / 'processed_consolidado.db'
REPORT_PATH = LOGS / 'overnight_report.txt'

# Import shared utils
sys.path.append(str((ROOT / 'portable_app' / 'src').resolve()))
from utils.unified_text import unified_text_preprocessing
from utils.year_range_database import YearRangeDatabaseOptimizer


def _strip_accents(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize('NFKD', s)
    return ''.join(ch for ch in s if not unicodedata.combining(ch))


def validate_db() -> Dict[str, int]:
    stats = {}
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    for t in ['processed_consolidado', 'sku_year_ranges', 'vin_prefix_frequencies']:
        try:
            cur.execute(f'SELECT COUNT(*) FROM {t}')
            stats[t] = cur.fetchone()[0]
        except Exception as e:
            stats[t] = -1
    con.close()
    return stats


def top_referencias(n: int = 30) -> List[Tuple[str, str, str, str, int, int, int]]:
    """Return list of (maker, series, descripcion, referencia, start_year, end_year, global_freq)
    for the most frequent referencias overall.
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        '''
        SELECT maker, series, descripcion, referencia, start_year, end_year, global_sku_frequency
        FROM sku_year_ranges
        ORDER BY global_sku_frequency DESC
        LIMIT ?
        ''', (n,)
    )
    rows = cur.fetchall()
    con.close()
    return rows


def find_any_vin(maker: str, model: int, series: str) -> str | None:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        '''
        SELECT vin_number FROM processed_consolidado
        WHERE maker = ? AND model = ? AND series = ? AND vin_number IS NOT NULL AND LENGTH(vin_number)=17
        LIMIT 1
        ''', (maker.lower(), model, series.lower())
    )
    row = cur.fetchone()
    con.close()
    return row[0] if row else None


def choose_model_within_range(maker: str, series: str, ref: str, start_year: int, end_year: int) -> int | None:
    """Pick the median year within the range that exists in processed_consolidado for this maker/series/ref."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        '''
        SELECT model, COUNT(*) as c FROM processed_consolidado
        WHERE maker=? AND series=? AND referencia=? AND model BETWEEN ? AND ?
        GROUP BY model ORDER BY c DESC
        ''', (maker.lower(), series.lower(), ref, start_year, end_year)
    )
    rows = cur.fetchall()
    con.close()
    if rows:
        return int(rows[0][0])
    # fallback to middle of range
    if start_year and end_year:
        return (int(start_year) + int(end_year)) // 2
    return None


def run_predictions(cases):
    opt = YearRangeDatabaseOptimizer(str(DB_PATH))
    results = []
    for maker, series, descripcion, ref, s_year, e_year, gfreq in cases:
        # pick model
        model = choose_model_within_range(maker, series, ref, s_year, e_year)
        if model is None:
            results.append({
                'maker': maker, 'series': series, 'model': None, 'descripcion': descripcion,
                'referencia': ref, 'global_freq': gfreq, 'status': 'no_model_in_range'
            })
            continue
        vin = find_any_vin(maker, model, series)
        norm_desc = unified_text_preprocessing(descripcion or '')
        preds_orig = opt.get_sku_predictions_year_range(maker, model, series, descripcion or '', limit=10)
        preds_norm = opt.get_sku_predictions_year_range(maker, model, series, norm_desc or '', limit=10)
        def to_list(preds):
            return [p['sku'] for p in preds]
        found = (ref in to_list(preds_orig)) or (ref in to_list(preds_norm))
        results.append({
            'maker': maker, 'series': series, 'model': model, 'vin': vin,
            'descripcion': descripcion, 'normalized': norm_desc,
            'referencia': ref, 'global_freq': gfreq,
            'preds_orig': to_list(preds_orig), 'preds_norm': to_list(preds_norm),
            'status': 'PASS' if found else 'MISS'
        })
    opt.close()
    return results


def analyze_noun_gender(limit:int=200000, topn:int=80) -> Dict[str, List[Tuple[str,int]]]:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    q = f"SELECT normalized_descripcion FROM processed_consolidado WHERE normalized_descripcion IS NOT NULL LIMIT {limit}"
    DIR = {'izquierdo','izquierda','derecho','derecha','delantero','delantera','trasero','trasera'}
    right_after = Counter()
    left_before = Counter()
    for (t,) in cur.execute(q):
        s = (t or '').lower().replace('.', ' ').replace('/', ' ')
        toks = re.findall(r"[a-z0-9áéíóúñ]+", s)
        for i, tok in enumerate(toks):
            if tok in DIR:
                if i+1 < len(toks):
                    right_after[_strip_accents(toks[i+1])] += 1
                if i-1 >= 0:
                    left_before[_strip_accents(toks[i-1])] += 1
    con.close()
    def top_unknown(cnt: Counter, topn:int):
        out = []
        for w, c in cnt.most_common(topn*3):
            if w in DIR:
                continue
            out.append((w, c))
            if len(out) >= topn:
                break
        return out
    return {
        'right_after': top_unknown(right_after, topn),
        'left_before': top_unknown(left_before, topn),
    }


def main():
    lines = []
    lines.append('=== OVERNIGHT VALIDATION REPORT ===')
    lines.append(f'DB: {DB_PATH}')
    stats = validate_db()
    lines.append('Table counts: ' + json.dumps(stats))

    cases = top_referencias(30)
    lines.append(f'Top referencias: {len(cases)} rows')

    results = run_predictions(cases)
    passes = sum(1 for r in results if r.get('status')=='PASS')
    misses = sum(1 for r in results if r.get('status')=='MISS')
    lines.append(f'Prediction check: PASS={passes}, MISS={misses}')
    for r in results:
        header = f"{r['maker']} | {r['series']} | {r.get('model')} | ref={r['referencia']} | gfreq={r['global_freq']} | status={r['status']}"
        lines.append(header)
        lines.append(f"  VIN={r.get('vin')} | desc='{r['descripcion']}' | norm='{r['normalized']}'")
        if r['status']!='no_model_in_range':
            lines.append(f"  preds_orig={r['preds_orig']}")
            lines.append(f"  preds_norm={r['preds_norm']}")

    # Analyzer
    lines.append('\n=== Noun Gender Analyzer (candidates) ===')
    ng = analyze_noun_gender()
    lines.append('Right-after candidates (likely head nouns):')
    for w,c in ng['right_after']:
        lines.append(f'{w},{c}')
    lines.append('\nLeft-before candidates:')
    for w,c in ng['left_before']:
        lines.append(f'{w},{c}')

    REPORT_PATH.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Wrote report to {REPORT_PATH}')

if __name__ == '__main__':
    main()

