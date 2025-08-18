#!/usr/bin/env python3
"""
Add a hyperlink in NewAbbreviations2 sheet to run the promotions runner.
Places link in J1 to avoid interfering with header columns.
"""
from __future__ import annotations
import os
import openpyxl

ROOT = os.path.dirname(os.path.dirname(__file__))
XLSX = os.path.join(ROOT, 'Source_Files', 'Text_Processing_Rules.xlsx')
BATCH = os.path.join(ROOT, 'scripts', 'close_excel_then_run.bat')


def main():
    if not os.path.exists(XLSX):
        raise SystemExit(f"Rules file not found: {XLSX}")
    if not os.path.exists(BATCH):
        raise SystemExit(f"Runner not found: {BATCH}")

    wb = openpyxl.load_workbook(XLSX)
    if 'NewAbbreviations2' not in wb.sheetnames:
        raise SystemExit("Sheet 'NewAbbreviations2' not found. Generate it first.")
    sh = wb['NewAbbreviations2']

    cell = sh['J1']
    cell.value = '▶ Run Promotions (auto-closes Excel + runs data processor)'
    cell.hyperlink = os.path.abspath(BATCH)
    cell.style = 'Hyperlink'

    wb.save(XLSX)
    print('Added hyperlink to NewAbbreviations2! Cell J1.')


if __name__ == '__main__':
    main()

