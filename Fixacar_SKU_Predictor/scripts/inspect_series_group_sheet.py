#!/usr/bin/env python3
import os, openpyxl
ROOT = os.path.dirname(os.path.dirname(__file__))
XLSX = os.path.join(ROOT, 'Source_Files', 'Text_Processing_Rules.xlsx')
SHEET = 'Series_Group_Candidates (2)'
wb = openpyxl.load_workbook(XLSX)
if SHEET not in wb.sheetnames:
    print('MISSING_SHEET')
else:
    sh = wb[SHEET]
    headers = [sh.cell(1,i).value for i in range(1, sh.max_column+1)]
    print('HEADERS:', headers)
    print('N_COLS:', sh.max_column)
    print('N_ROWS:', sh.max_row)
    for r in range(2, min(sh.max_row, 6)+1):
        row = [sh.cell(r,i).value for i in range(1, sh.max_column+1)]
        print('ROW', r, ':', row)

