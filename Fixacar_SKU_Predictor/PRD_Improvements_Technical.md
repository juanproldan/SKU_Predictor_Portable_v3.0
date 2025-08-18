# PRD – Improvements Plan (Technical)

This document lists the concrete technical improvements to implement next for Fixacar SKU Predictor v3.0 while preserving the client's constraints: portable (Win10/11; x64 & ARM64), simple, predictable, and no heavy dependencies. It complements PRD_Fixacar_v3.0.md.

## 0) Goals and Non‑Goals
- Goals
  - Raise SKU top‑1 accuracy without adding heavy runtime dependencies
  - Keep Step 5 GUI identical in behavior; only internal quality/robustness changes
  - Maintain a single canonical data folder: Source_Files/
- Non‑Goals
  - No re‑introduction of spaCy or large DL frameworks
  - No new Excel exports from Step 5; continue appending Maestro only
  - No revival of the deprecated User_Corrections sheet

## 1) Step 2 – Text Processing & Data Build

### 1.1 Deterministic normalization pipeline
- Enforce this exact order in `portable_app/src/utils/unified_text.py`:
  1) input (original casing) → to string
  2) lowercase + accent strip
  3) phrase‑level abbreviations (Pairs sheet)
  4) token‑level abbreviations (Abbreviations sheet)
  5) equivalencias (canonical mapping)
  6) adjective gender agreement using Noun_Gender
  7) whitespace/dup hyphen cleanup
- Add unit/smoke tests to lock behavior. Extend `scripts/smoke_test_text_normalization.py` to ~20 cases covering: front/rear/left/right, paragolpes, lights, mirrors, and tricky bigrams.

Acceptance:
- All smoke tests pass deterministically on repeated runs
- No plural→singular reduction occurs anywhere

### 1.2 Phrase Abbreviations workflow hardening
- `scripts/ensure_phrase_abbreviations_sheet.py`:
  - Validate sheet presence and columns: [From_Phrase, To_Phrase, Confidence, Notes]
  - Ensure Confidence ∈ {high, medium, low}; only high/medium used automatically
- `scripts/promote_abbreviations_pairs.py`:
  - Idempotent promotions from NewAbbreviations2 → Abbreviations Pairs sheet
  - Collision detection: same From_Phrase with multiple To_Phrase → log to `logs/02_new_abbreviations_pairs.log` and skip
  - Keep `Promotions_Log` sheet with timestamp, from→to, author (optional)

Acceptance:
- Running the promotion twice produces no duplicate rows
- Conflicts are logged and not auto‑promoted

### 1.3 Noun_Gender sourcing guardrails
- `scripts/update_noun_gender.py`:
  - Feed only nouns: exclude tokens from a stoplist (izq, der, tra, del, post, etc.), digits, and tokens <3 chars
  - Append only new nouns; never edit existing rows
  - Allow blank gender for unknowns; experts can fill later

Acceptance:
- Re‑running appends only previously unseen nouns

### 1.4 VIN validation & enrichment
- Utilities (new or in `unified_consolidado_processor.py`):
  - Always uppercase; replace I→1, O/Q→0
  - Hard invalid if length != 17
  - Hard invalid if 6 last positions all identical (e.g., 000000)
  - Optional: check digit (ISO 3779) for regions where applicable; if fails, mark “suspect” but do not drop if policy forbids
  - Maintain `Source_Files/WMI.csv` mapping WMI→maker; if unknown WMI, flag for review
  - Keep/refresh `VIN_prefix_frequencies` logs

Acceptance:
- Processor logs counts of rejected/suspect VINs and unknown WMIs

### 1.5 Database build improvements
- In `unified_consolidado_processor.py` and `utils/year_range_database.py`:
  - Clamp year to [1990, current_year + 2] BEFORE aggregation; drop outliers with a counter
  - Create deterministic indexes; run ANALYZE only once during build
  - Add `metadata` table: processor_version, rules_checksum, row_counts, build_timestamp

Acceptance:
- sku_year_ranges has no out‑of‑range years; metadata present and correct

## 2) Step 3 – VIN Lookup Enhancements
- Load `Source_Files/WMI.csv` at startup; map VIN→(maker, region) if WMI known
- If WMI unknown, keep current behavior; optionally bias predictions by known maker signals from text normalization

Acceptance:
- For VINs with known WMI, predicted maker aligns with mapping ≥ 99% of the time (spot‑check sample)

## 3) Step 4 – SKU Scoring Enhancements (No new deps)

### 3.1 Probabilistic smoothing and back‑off
- Let C(key) be frequency for (maker, series, normalized_descripcion, referencia) within valid years
- Use Laplace smoothing: C′ = C + α (α≈0.5) and normalize to probabilities
- Back‑off hierarchy when few counts or missing:
  1) (maker, series, normalized_descripcion)
  2) (maker, normalized_descripcion)
  3) (normalized_descripcion)
- Combine with VIN prior: if VIN indicates a maker/series, multiply that branch by factor β (β≈1.2–1.5)

### 3.2 Tie‑breaking by similarity (pure SQLite option)
- Add optional re‑rank for top K (e.g., K=10):
  - Use SQLite FTS5 virtual table over normalized_descripcion to compute BM25, or
  - Compute tri‑gram Jaccard similarity in Python for K candidates
- Final score = λ·probability + (1−λ)·similarity (λ≈0.7)

### 3.3 Confidence score and explainability
- Confidence = calibrated function of: normalized probability gap top1–top2, year overlap with query VIN (if available), and evidence count z‑score
- Display the first DB evidence label only, as required

Acceptance:
- Unit test scoring on controlled toy data; monotonicity checks (more evidence ⇒ higher score)

## 4) Optional "Tiny Helper" Model (Portable)

Purpose: Only break ties when the frequency model is uncertain.

Training (developer machine; not needed on client):
- Build TF‑IDF over n‑grams of (maker + series + normalized_descripcion)
- Classifier: LogisticRegression/LinearSVC (scikit‑learn)
- Export to ONNX (skl2onnx).

Inference (client runtime):
- Add `onnxruntime` (CPU only). Load `models/sku/tfidf_linear.onnx` and vectorizer `tfidf.pkl`.
- Only run when top1−top2 gap < threshold (e.g., <0.05) and K candidates exist.

Files:
- `models/sku/tfidf_linear.onnx` (≈ 5–30 MB)
- `models/sku/tfidf.pkl` (≈ 1–5 MB)

Acceptance:
- A/B on a held‑out slice shows +3–6% top‑1 on ambiguous cases

## 5) Step 5 – GUI & Runtime
- Add prediction cache (LRU, size≈500 keys) at the service layer to speed repeats
- Async candidate fetch when needed; keep UI responsive
- "Why this SKU?" panel: show top 3 reasons (evidence count, year overlap, maker match)
- Maestro append behavior unchanged

## 6) Implementation Plan & Owners
- Phase A (no new deps)
  - A1 Text normalization order + tests
  - A2 Abbrev workflow validation + idempotent promotions
  - A3 Noun_Gender guardrails
  - A4 VIN validation + WMI.csv + logs
  - A5 DB build: clamp years, indexes, metadata
  - A6 Scoring: smoothing, back‑off, similarity tie‑break, confidence
- Phase B (optional tiny helper)
  - B1 Training script (sklearn) + export to ONNX
  - B2 Integrate onnxruntime scorer gated by tie threshold
  - B3 A/B evaluate, keep toggleable by config

## 7) Testing & Verification
- Smoke tests: `py -3.11 Fixacar_SKU_Predictor/scripts/smoke_test_text_normalization.py`
- Data processor run: `2_run_data_processor.bat` (or Python script equivalent) — verify logs and metadata table
- Unit tests for scoring and back‑off (add `scripts/test_parity_and_db.py` cases)
- A/B evaluation script (optional) to compare baseline vs. helper model

## 8) Risks & Mitigations
- Rule conflicts (phrase vs token abbreviations): detect & log; prefer phrase-level
- ONNX helper drift: retrain schedule every 2–4 weeks; keep versioned models
- FTS5 availability: if SQLite build lacks FTS5, use Python tri‑gram fallback

## 9) Deliverables
- Updated scripts: ensure/promote abbreviations, noun gender updater, processor, scoring utils
- New `WMI.csv`, new smoke tests, DB metadata table
- Optional: ONNX model + vectorizer; runtime guarded by config flag

