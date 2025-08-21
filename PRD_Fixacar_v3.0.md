# PRD_Fixacar_v3.0 — Product Requirements Document (Portable Edition)

This document is the single source of truth for the Fixacar SKU Predictor v3.0 portable implementation. It reflects the client's confirmed preferences and constraints.

## 1. Scope and Goals
- Replicate legacy Step 5 GUI behavior with modern, lightweight backends.
- Keep data and rules centralized in Source_Files/.
- Provide a clean, portable Windows client (Win10/11; x64 and ARM64 friendly).
- Prioritize real, permanent fixes over workarounds or suppressions.

## 2. Canonical Data Locations (Source_Files/)
- Consolidado.json — input (ignored by Git)
- processed_consolidado.db — generated output (ignored by Git; always rebuilt)
- Text_Processing_Rules.xlsx — tracked in Git (must include Noun_Gender and Maestro sheets)

## 3. Processing Pipeline (Step 2)
- Implemented in scripts/02_process_data_polars.py and portable_app/src/.
- Always rebuild processed_consolidado.db from Consolidado.json (no reuse of old DBs).
- Normalize text centrally via portable_app/src/utils/unified_text.py:
  - Lowercase and accent-strip for processing.
  - Abbreviation expansion (token-level) and phrase-level expansions (Abbreviations_Phrases) with support for dots/slashes as separators (e.g., 'tra.d.' -> 'tra d'); equivalencias only for matching groups, not canonicalization.
  - Series normalization via Series tab (map variants to canonical, case-insensitive).
  - Targeted adjective agreement using Noun_Gender entries (no spaCy).
  - Adjective agreement: direction/location adjectives (trasero/a, delantero/a, izquierdo/a, derecho/a) agree with the nearest known noun gender (Noun_Gender sheet + internal extras for 'puerta', 'rejilla', 'paragolpes', 'reflector').
- Maker, series, descripcion, normalized_descripcion are consistently lowercase in DB.

- Series normalization is space-insensitive: inputs and mapping keys are uppercased, trimmed, and inner whitespace is collapsed (e.g., 'CX  30' → 'CX 30'). This prevents duplicates caused by stray spaces.

### 3.1 Model year policy (critical)
- Valid model years = 1990 through current_year + 2 (e.g., 2027 at time of writing).
  - Anything outside this interval is treated as missing and excluded from aggregations.
  - Prevents 0-year and out-of-scope ranges in sku_year_ranges.
- sku_year_ranges aggregates by (maker, series, descripcion, normalized_descripcion, referencia) and computes start_year = MIN(model), end_year = MAX(model) within the valid range.

- Early year gating: records with model outside [year_start, current_year+2] are skipped before insertion (configurable via Source_Files/config.json).
- VIN prefix and SKU aggregates rely on in-range data only by construction (no duplicate year filters needed downstream).
- VIN prefix grouping in vin_prefix_frequencies uses the 11-character prefix (positions 1–11) with positions 12–17 masked as 'X'. Distinct characters at any position 1–11 (e.g., position 8 differing between '3MVDM2W7ANL' and '3MVDM2WLANL') will produce separate lines by design, as they encode different configurations.


## 4. VIN Handling
- VIN normalization only fixes characters (I→1, O/Q→0; uppercase).
- Validation utilities exist, but strict VIN filtering is off per client instruction for Step 2. Records must not be dropped solely due to VIN.

## 5. Step 5 GUI (SKU Predictor)
- Must behave like the legacy app; no new Excel exports from the predictor.
- Maestro entries are stored in the Maestro sheet inside Text_Processing_Rules.xlsx (no standalone Maestro.xlsx required).
- Uses sku_year_ranges for frequency- and year-aware SKU prediction.

## 6. Text_Processing_Rules.xlsx
- Tabs used: Equivalencias, Abbreviations, Series, Noun_Gender, Maestro.
- Deprecated: User_Corrections (no longer read or written by any script).
- Noun_Gender sheet requirements:
  - Columns: noun, gender (m/f).
  - Content derived from normalized descriptions; abbreviations (iz, der, tra, etc.) must not be added as nouns.
  - Auto-population script (scripts/auto_populate_noun_gender.py) fills genders using explicit domain lists and conservative morphology; unknowns may be inserted with blank gender for later review.

## 7. Folder and Deployment Rules
- Clean client bundle:
  - Only essential launchers in root; all other assets organized in subfolders.
  - No duplicated data/models folders. Source_Files is the single canonical data folder.
- Keep PRDs and TODOs under version control; never delete them during cleans.

## 8. Compatibility & Stack
- Python 3.11.x portable; ARM64-friendly where possible.
- No spaCy dependency in client build (remove from project/repo).
- Prefer Polars/SQLite and small local utilities; avoid heavyweight NLP.

## 9. Testing & Verification
- After code changes:
  - Rebuild processed_consolidado.db.
  - Verify sku_year_ranges contains no entries with start_year or end_year outside the valid model range.
  - Run noun-gender updater and spot-check Text_Processing_Rules.xlsx.

## 10. Change Control
- Any behavior changes to Step 5 or text normalization require prior review against legacy behavior and this PRD.
- Keep this PRD updated with any approved policy changes (e.g., year bounds).

