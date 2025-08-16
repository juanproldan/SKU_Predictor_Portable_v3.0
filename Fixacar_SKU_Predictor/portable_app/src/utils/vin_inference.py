"""
VIN inference-only helpers used by the GUI and portable app.

This module intentionally avoids importing training stacks (sklearn/torch/etc).
It provides only light-weight utilities needed for VIN feature extraction during
inference.
"""
from __future__ import annotations
import re


def clean_vin_for_production(vin: str | None) -> str | None:
    """Lenient VIN cleaning for production.
    - Returns uppercase 17-char VIN or None if invalid.
    - Excludes I, O, Q per VIN standard.
    """
    if not vin:
        return None
    vin_str = str(vin).upper().strip()
    if len(vin_str) != 17:
        return None
    if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", vin_str):
        return None
    return vin_str


def extract_vin_features_production(vin: str | None):
    """Extract minimal VIN features for prediction in production.
    Returns dict or None if invalid.
    """
    cleaned_vin = clean_vin_for_production(vin)
    if not cleaned_vin:
        return None
    return {
        "wmi": cleaned_vin[0:3],
        "vds": cleaned_vin[3:8],
        "year_code": cleaned_vin[9],
        "plant_code": cleaned_vin[10],
        "vds_full": cleaned_vin[3:9],
    }


# === VIN Year decoding (context-aware) ===

_DEF_YEAR_MAP = {
    'A': [1980, 2010], 'B': [1981, 2011], 'C': [1982, 2012], 'D': [1983, 2013],
    'E': [1984, 2014], 'F': [1985, 2015], 'G': [1986, 2016], 'H': [1987, 2017],
    'J': [1988, 2018], 'K': [1989, 2019], 'L': [1990, 2020], 'M': [1991, 2021],
    'N': [1992, 2022], 'P': [1993, 2023], 'R': [1994, 2024], 'S': [1995, 2025],
    'T': [1996, 2026], 'V': [1997, 2027], 'W': [1998, 2028], 'X': [1999, 2029],
    'Y': [2000, 2030], '1': [2001, 2031], '2': [2002, 2032], '3': [2003, 2033],
    '4': [2004, 2034], '5': [2005, 2035], '6': [2006, 2036], '7': [2007, 2037],
    '8': [2008, 2038], '9': [2009, 2039]
}


def decode_year_with_context(year_code: str | None, context_year: int | None = None) -> int | None:
    """Decode VIN year code with modern context bias (2010–2029 for letters).
    Returns an int year or None if unknown.
    """
    if not year_code:
        return None
    year_code = str(year_code).upper().strip()
    if year_code not in _DEF_YEAR_MAP:
        return None
    years = _DEF_YEAR_MAP[year_code]
    # For modern DBs, prefer later year for letters, earlier for digits
    if year_code in 'ABCDEFGHJKLMNPRSTVWX':
        return years[1]
    return years[0]


def decode_year(year_code: str | None) -> int | None:
    return decode_year_with_context(year_code)

