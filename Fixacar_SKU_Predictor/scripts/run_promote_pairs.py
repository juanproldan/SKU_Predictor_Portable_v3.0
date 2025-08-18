#!/usr/bin/env python3
"""
Runner to safely execute promote_abbreviations_pairs while Excel is open.
- Waits for Excel to release Text_Processing_Rules.xlsx (checks for ~${name}.xlsx lock file)
- Runs the promotion
- Reopens the workbook for the user
"""
from __future__ import annotations
import os
import sys
import time
import traceback

ROOT = os.path.dirname(os.path.dirname(__file__))
RULES_XLSX = os.path.join(ROOT, 'Source_Files', 'Text_Processing_Rules.xlsx')
LOCKFILE = os.path.join(os.path.dirname(RULES_XLSX), '~$' + os.path.basename(RULES_XLSX))
SCRIPTS_DIR = os.path.join(ROOT, 'scripts')


def _wait_for_excel_close(timeout_seconds: int | None = None) -> None:
    start = time.time()
    printed_hint = False
    while True:
        locked = os.path.exists(LOCKFILE)
        if not locked:
            # Also try a quick open-for-append test in case lockfile is missing but handle is held
            try:
                with open(RULES_XLSX, 'ab') as _:
                    pass
                return
            except Exception:
                locked = True
        if not printed_hint:
            print('Please close Excel (Text_Processing_Rules.xlsx) so promotions can proceed...')
            printed_hint = True
        if timeout_seconds is not None and (time.time() - start) > timeout_seconds:
            raise TimeoutError('Timed out waiting for Excel to close the workbook.')
        time.sleep(1.0)


def main() -> int:
    print('== Promote Abbreviations Pairs Runner ==')
    if not os.path.exists(RULES_XLSX):
        print(f'Rules file not found: {RULES_XLSX}')
        return 2

    # Ensure we can import the promotion script
    if SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, SCRIPTS_DIR)

    print('Waiting for Excel to close the workbook if it is open...')
    try:
        _wait_for_excel_close()
    except Exception as e:
        print(f'Warning: {e}. Will attempt to run promotions anyway...')

    try:
        from promote_abbreviations_pairs import promote
    except Exception:
        traceback.print_exc()
        print('Failed to import promote_abbreviations_pairs.py')
        return 3

    try:
        promote()
        print('Promotions completed successfully.')
    except Exception:
        traceback.print_exc()
        print('Promotion run failed.')
        return 4
    # Do not reopen workbook here; caller (batch) will reopen after all steps
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

