#!/usr/bin/env python3
"""
Promote vetted (Word, Abbr. 1) pairs from NewAbbreviations2 to Abbreviations.

- Reads Text_Processing_Rules.xlsx -> NewAbbreviations2
- For each row where Approve? == 'Y' and Abbr. 1 not empty:
  - If Word is empty, the row is skipped (expert should fill Word)
  - Adds the abbreviation under that Word in Abbreviations (next empty Abbr.* column)
  - Deduplicates if the abbreviation already exists for that word
- Appends the promoted rows to NewAbbreviations2_History with timestamp
- Deletes promoted rows from NewAbbreviations2

Run:
  python Fixacar_SKU_Predictor/scripts/promote_abbreviations_pairs.py
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'Source_Files'
XLSX = SRC / 'Text_Processing_Rules.xlsx'


def ensure_sheet(wb, name: str):
    if name in wb.sheetnames:
        return wb[name]
    return wb.create_sheet(name)


def collect_existing(sh_abbr) -> Dict[str, Set[str]]:
    existing: Dict[str, Set[str]] = {}
    for r in range(2, sh_abbr.max_row + 1):
        word = (sh_abbr.cell(r, 1).value or '').strip().lower()
        if not word:
            continue
        c = 2
        abbrs: Set[str] = set()
        while c <= sh_abbr.max_column and (sh_abbr.cell(1, c).value or '').strip().lower().startswith('abbr'):
            v = (sh_abbr.cell(r, c).value or '').strip().lower()
            if v:
                abbrs.add(v)
            c += 1
        if word:
            existing[word] = existing.get(word, set()) | abbrs
    return existing


def append_abbr(sh_abbr, word: str, abbr: str):
    # Find row for word or create
    row_idx = None
    for r in range(2, sh_abbr.max_row + 1):
        if (sh_abbr.cell(r, 1).value or '').strip().lower() == word:
            row_idx = r
            break
    if row_idx is None:
        row_idx = sh_abbr.max_row + 1
        sh_abbr.cell(row_idx, 1, word)
    # Find next empty Abbr.* column
    c = 2
    while c <= sh_abbr.max_column and (sh_abbr.cell(row_idx, c).value or ''):
        c += 1
    sh_abbr.cell(row_idx, c, abbr)


def promote():
    if not XLSX.exists():
        raise SystemExit(f"Rules file not found: {XLSX}")

    wb = openpyxl.load_workbook(XLSX)
    sh_new = ensure_sheet(wb, 'NewAbbreviations2')
    sh_hist = ensure_sheet(wb, 'NewAbbreviations2_History')
    sh_abbr = ensure_sheet(wb, 'Abbreviations')

    # Ensure history headers
    if sh_hist.max_row == 1:
        for c in range(1, sh_new.max_column + 1):
            sh_hist.cell(1, c, sh_new.cell(1, c).value)
        sh_hist.cell(1, sh_new.max_column + 1, 'Promoted_At')

    # Existing pairs
    existing = collect_existing(sh_abbr)

    # Find columns
    headers = { (sh_new.cell(1, c).value or '').strip().lower(): c for c in range(1, sh_new.max_column + 1) }
    col_word = headers.get('word', 1)
    col_abbr = headers.get('abbr. 1', 2)
    col_approve = headers.get('approve?')
    if not col_approve:
        raise SystemExit("NewAbbreviations2 sheet is missing 'Approve?' column.")

    promoted_rows: List[int] = []

    for r in range(2, sh_new.max_row + 1):
        approve = (sh_new.cell(r, col_approve).value or '').strip().lower()
        if approve != 'y':
            continue
        word = (sh_new.cell(r, col_word).value or '').strip().lower()
        abbr = (sh_new.cell(r, col_abbr).value or '').strip().lower()
        if not abbr or not word:
            continue
        if abbr in existing.get(word, set()):
            promoted_rows.append(r)
            continue
        append_abbr(sh_abbr, word, abbr)
        existing.setdefault(word, set()).add(abbr)
        promoted_rows.append(r)

    # Archive and delete
    if promoted_rows:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for r in promoted_rows:
            dest_row = sh_hist.max_row + 1
            for c in range(1, sh_new.max_column + 1):
                sh_hist.cell(dest_row, c, sh_new.cell(r, c).value)
            sh_hist.cell(dest_row, sh_new.max_column + 1, timestamp)
        for r in sorted(promoted_rows, reverse=True):
            sh_new.delete_rows(r, 1)

    wb.save(XLSX)
    print(f"Promotion complete. Promoted rows: {len(promoted_rows)}")


if __name__ == '__main__':
    promote()

