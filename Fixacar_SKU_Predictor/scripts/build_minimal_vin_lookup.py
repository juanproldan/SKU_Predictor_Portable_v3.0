#!/usr/bin/env python3
import os
import sqlite3
from collections import defaultdict
import joblib

ROOT = os.path.dirname(os.path.dirname(__file__))
DB = os.path.join(ROOT, 'Source_Files', 'processed_consolidado.db')
OUT = os.path.join(ROOT, 'portable_app', 'models', 'vin', 'lookup_model.joblib')

os.makedirs(os.path.dirname(OUT), exist_ok=True)

con = sqlite3.connect(DB)
c = con.cursor()
q = (
    "select substr(vin_number,1,3) as wmi, substr(vin_number,4,3) as vds, "
    "maker, model, series, count(*) as c "
    "from processed_consolidado "
    "where vin_number is not null and length(vin_number)=17 and maker is not null and series is not null "
    "group by 1,2,3,4,5"
)
c.execute(q)
rows = c.fetchall()
con.close()

freq = defaultdict(lambda: defaultdict(int))
for wmi, vds, maker, model, series, cnt in rows:
    key = (wmi, vds)
    val = (maker, model, series)
    freq[key][val] += cnt

lookup = {}
for key, mapc in freq.items():
    (maker, model, series), _ = max(mapc.items(), key=lambda kv: kv[1])
    lookup[key] = {"maker": maker, "model": str(model), "series": series}

joblib.dump(lookup, OUT)
print("VIN lookup saved:", OUT, "keys:", len(lookup))

