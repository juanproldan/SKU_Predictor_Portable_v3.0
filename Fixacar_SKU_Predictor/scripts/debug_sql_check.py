import sqlite3, os

root = os.path.join(os.path.dirname(__file__), '..')
root = os.path.abspath(root)
path = os.path.join(root, 'Source_Files', 'processed_consolidado.db')
print('DB path:', path)
print('DB exists:', os.path.exists(path))
con = sqlite3.connect(path)
cur = con.cursor()

maker = 'Chevrolet'
series = 'Spark'
year = 2017
terms = [
    'farola izquierda',
    'guardafango izquierdo',
    'guardapolvo plastico delantero izquierdo',
    'capo',
]

print('\nTop 15 entries for maker/series/year regardless of description:')
cur.execute('''
  SELECT descripcion, normalized_descripcion, referencia, frequency, start_year, end_year
  FROM sku_year_ranges
  WHERE LOWER(maker)=LOWER(?) AND LOWER(series)=LOWER(?) AND ? BETWEEN start_year AND end_year
  ORDER BY frequency DESC
  LIMIT 15
''', (maker, series, year))
for r in cur.fetchall():
    print('  -', r)

for t in terms:
    print('\n=== Term:', t, '===')
    # Exact
    cur.execute('''
      SELECT referencia, frequency, start_year, end_year
      FROM sku_year_ranges
      WHERE LOWER(maker)=LOWER(?) AND LOWER(series)=LOWER(?)
        AND (LOWER(descripcion)=LOWER(?) OR LOWER(normalized_descripcion)=LOWER(?))
        AND ? BETWEEN start_year AND end_year
      ORDER BY frequency DESC LIMIT 10
    ''', (maker, series, t, t, year))
    exact = cur.fetchall()
    print('Exact matches:', exact)

    # LIKE fuzzy
    like = f'%{t.lower()}%'
    cur.execute('''
      SELECT referencia, frequency, start_year, end_year, descripcion
      FROM sku_year_ranges
      WHERE LOWER(maker)=LOWER(?) AND LOWER(series)=LOWER(?)
        AND (LOWER(descripcion) LIKE ? OR LOWER(normalized_descripcion) LIKE ?)
        AND ? BETWEEN start_year AND end_year
      ORDER BY frequency DESC LIMIT 10
    ''', (maker, series, like, like, year))
    fuzzy = cur.fetchall()
    print('Fuzzy matches count:', len(fuzzy))
    for r in fuzzy:
        print('  ->', r)

print('\nDistinct descriptions (top 30 by frequency) for Spark 2017:')
cur.execute('''
  SELECT descripcion, SUM(frequency) as fsum
  FROM sku_year_ranges
  WHERE LOWER(maker)=LOWER(?) AND LOWER(series)=LOWER(?) AND ? BETWEEN start_year AND end_year
  GROUP BY descripcion
  ORDER BY fsum DESC
  LIMIT 30
''', (maker, series, year))
for d, f in cur.fetchall():
    print('  ', f, 'x', d)

con.close()

