from pathlib import Path
import sys
root = Path('.').resolve()
src = root/'Fixacar_SKU_Predictor'/'portable_app'/'src'
sys.path.append(str(src))
from utils.year_range_database import YearRangeDatabaseOptimizer
opt = YearRangeDatabaseOptimizer(str(root/'Fixacar_SKU_Predictor'/'Source_Files'/'processed_consolidado.db'))
print('Variant probe start')
for series in ['2', '2 [2] [fl]', '2(dj/dl)/basico']:
    res = opt.get_sku_predictions_year_range('mazda', 2020, series, 'paragolpes del.', limit=5)
    print(series, '->', res[:3])
opt.close()

