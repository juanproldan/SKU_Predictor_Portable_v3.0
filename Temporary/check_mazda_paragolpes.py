import sqlite3, os
from pathlib import Path
root = Path(__file__).resolve().parents[1]
db = root/'Fixacar_SKU_Predictor'/'Source_Files'/'processed_consolidado.db'
con = sqlite3.connect(db)
cur = con.cursor()

maker='mazda'
desc='paragolpes del.'
ndesc='paragolpes delantero'
year=2019

print('Searching approved table for maker=mazda, year=2019, desc variants...')
cur.execute("""
SELECT maker, series, descripcion, normalized_descripcion, referencia, start_year, end_year, frequency, global_sku_frequency
FROM sku_year_ranges_Aprobado
WHERE maker = ? AND (? BETWEEN start_year AND end_year)
AND (descripcion = ? OR normalized_descripcion = ?)
ORDER BY frequency DESC
""", (maker, year, desc, ndesc))
rows = cur.fetchall()
print('rows:', len(rows))
for r in rows[:20]:
    print(r)

# Show if DB5J50031EBB appears broadly for mazda 2 in that year
cur.execute("""
SELECT maker, series, referencia, descripcion, normalized_descripcion, start_year, end_year, frequency
FROM sku_year_ranges_Aprobado
WHERE maker=? AND (? BETWEEN start_year AND end_year) AND referencia='DB5J50031EBB'
ORDER BY frequency DESC
""", (maker, year))
rows2 = cur.fetchall()
print('Rows with referencia DB5J50031EBB in 2019:', len(rows2))
for r in rows2[:20]:
    print(r)

con.close()

