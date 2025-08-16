#!/usr/bin/env python3
"""
Minimal smoke tests for unified text processor:
- Ensure no plural→singular normalization
- Ensure gender agreement uses noun gender (paragolpes -> delantero)
Run: py -3.11 Fixacar_SKU_Predictor/scripts/smoke_test_text_normalization.py
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str((ROOT / 'portable_app' / 'src').resolve()))

from utils.unified_text import unified_text_preprocessing

CASES = [
    ("tapa paragolpes del.", "tapa paragolpes delantero"),
    ("soporte paragolpes del.", "soporte paragolpes delantero"),
    ("farolas der.", "farolas derecha"),  # no plural reduction; feminine for farola
    ("luz antiniebla tra izq", "luz antiniebla trasera izquierda"),
]


def main():
    ok = True
    for src, expected in CASES:
        out = unified_text_preprocessing(src)
        print(f"IN : {src}")
        print(f"OUT: {out}")
        print(f"EXP: {expected}")
        match = (out == expected)
        print("OK " if match else "FAIL", "\n")
        ok = ok and match
    if not ok:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

