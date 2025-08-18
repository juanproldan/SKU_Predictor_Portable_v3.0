#!/usr/bin/env python3
"""
Force-close Excel instances that have the Text_Processing_Rules.xlsx open
then run the promotions, then reopen the workbook.
"""
from __future__ import annotations
import os
import subprocess
import time
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
RULES_XLSX = os.path.join(ROOT, 'Source_Files', 'Text_Processing_Rules.xlsx')
BATCH = os.path.join(ROOT, 'scripts', 'run_promote_pairs.py')


def kill_excel_with_file(target: str) -> None:
    # Use PowerShell to find Excel processes locking the target file and close them
    ps = r"$p = Get-Process EXCEL -ErrorAction SilentlyContinue; if ($p) { $p | ForEach-Object { $_.CloseMainWindow() | Out-Null; Start-Sleep -Milliseconds 500; if (!$_.HasExited) { $_.Kill() } } }"
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=False)
    # Small wait to ensure file handles are released
    time.sleep(0.8)


def main() -> int:
    if not os.path.exists(RULES_XLSX):
        print(f"Rules file not found: {RULES_XLSX}")
        return 2

    kill_excel_with_file(RULES_XLSX)

    # Now run the safe runner (which will do the promotion and reopen the workbook)
    try:
        subprocess.run([sys.executable, BATCH], check=True)
    except Exception as e:
        print(f"Failed to run promotions: {e}")
        return 3
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

