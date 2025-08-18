# Fixacar – Improvements Plan (Simple Summary)

This is the short, plain‑English version of what we’ll add next. It keeps the app simple and portable.

## What stays the same
- Same Step 5 screen/behavior
- Same single data folder (Source_Files)
- No heavy AI packages

## Step 2 – Clean the text and build the database
- Make the clean‑up steps always run in the same order and add a few quick tests
- Improve the “phrase shortcuts” list and prevent conflicts
- Grow the noun‑gender list safely (add only new nouns; don’t change old ones)
- Better VIN checks (reject obviously bad VINs; keep a small list of known prefixes)
- Make the database more reliable (fix bad years; add a small “build info” table)

## Step 3 – VIN help
- Use a small file (WMI.csv) to map VIN prefixes to car makers
- If unknown, keep current behavior

## Step 4 – Better scoring without adding heavy tools
- Make counts safer for rare cases (smoothing)
- Use smart fallbacks when data is scarce
- Add a simple “close‑match” search to break ties
- Show a confidence score and reasons

Expected benefit: about 2–3% better top guess, with no new software to install.

## Optional “tiny helper” (only if we want more accuracy)
- A small extra model to break ties when the app is unsure
- Runs fast on any laptop; you can retrain it monthly with one script
- Adds one small library to the runtime

Expected extra benefit: another ~3–6% top guess on tricky cases.

## Order of work
1) Do the “no new software” items above
2) Measure results
3) If we still want more accuracy, add the tiny helper

## Files we will add/change
- Scripts to check phrases, update nouns, and build the DB
- A small WMI.csv file (VIN prefix → maker)
- Extra quick tests for text cleaning
- Optional: one small model file (only if we choose the helper)

