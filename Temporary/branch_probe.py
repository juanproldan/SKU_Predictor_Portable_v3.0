from pathlib import Path
import sys
root = Path('.').resolve()
src = root/'Fixacar_SKU_Predictor'/'portable_app'/'src'
sys.path.append(str(src))
from utils.year_range_database import YearRangeDatabaseOptimizer
opt = YearRangeDatabaseOptimizer(str(root/'Fixacar_SKU_Predictor'/'Source_Files'/'processed_consolidado.db'))
print('BRANCH probe: mazda 2 2020 paragolpes del.')
print(opt.get_sku_predictions_year_range('mazda',2020,'2','paragolpes del.',limit=5))
opt.close()

