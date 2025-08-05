# Data Files Setup Instructions

## 📊 Required Data Files

The following large data files are required for the SKU Predictor to function but are **excluded from Git** due to GitHub's 100MB file size limit:

### 🔍 Missing Files:

1. **`portable_app/data/Consolidado.json`** (223 MB)
   - Main data source for SKU predictions
   - Contains automotive parts information

2. **`portable_app/data/processed_consolidado.db`** (782 MB)
   - Processed SQLite database
   - Optimized for fast queries

## 🚀 Setup Instructions

### Option 1: Copy from Original Project
If you have access to the original v2.0 project:

```bash
# Copy from v2.0 project (adjust path as needed)
copy "..\010_SKU_Predictor_v2.0\Fixacar_NUCLEAR_DEPLOYMENT\Fixacar_SKU_Predictor_CLIENT\Source_Files\Consolidado.json" "portable_app\data\"
copy "..\010_SKU_Predictor_v2.0\Fixacar_NUCLEAR_DEPLOYMENT\Fixacar_SKU_Predictor_CLIENT\Source_Files\processed_consolidado.db" "portable_app\data\"
```

### Option 2: Download from Source
If you need to recreate the data:

1. **Download original Consolidado.json** from your data source
2. **Place in `portable_app/data/` directory**
3. **Run the data processing script** to create the database

### Option 3: Contact Project Owner
Contact the project maintainer for access to the data files.

## 📁 Expected Directory Structure

After setup, your directory should look like:

```
020_SKU_Predictor_Portable_v3.0/
├── portable_app/
│   ├── data/
│   │   ├── Consolidado.json          ← 223 MB (you need to add this)
│   │   ├── processed_consolidado.db  ← 782 MB (you need to add this)
│   │   ├── Maestro.xlsx              ✅ (included in Git)
│   │   └── Text_Processing_Rules.xlsx ✅ (included in Git)
│   ├── src/                          ✅ (all source code included)
│   └── models/                       ✅ (all trained models included)
└── ...
```

## ⚠️ Important Notes

1. **File Sizes**: These files are large and will take time to download/copy
2. **Git Ignore**: These files are intentionally excluded from Git
3. **Local Only**: Keep these files local - don't try to commit them to Git
4. **Required**: The application will not work without these data files

## 🔧 Verification

After copying the files, verify they exist:

```bash
# Check if files exist (Windows)
dir portable_app\data\Consolidado.json
dir portable_app\data\processed_consolidado.db
```

## 🆘 Troubleshooting

- **File not found errors**: Ensure all 4 data files are in the correct locations
- **Permission errors**: Make sure you have write access to the directories
- **Size verification**: Check file sizes match the expected values above

---

**Note**: This separation allows the codebase to be shared via GitHub while keeping large data files local or distributed separately.
