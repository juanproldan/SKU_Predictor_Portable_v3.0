# 🚗 How to Run Fixacar SKU Predictor v3.0

## 🎯 **QUICK START - MAIN APPLICATION**

**To run the main SKU Predictor application:**

```bash
# Double-click this file or run from command line:
run_sku_predictor.bat
```

**OR use the Master Launcher:**

```bash
# Double-click this file for a menu interface:
0_MASTER_LAUNCHER.bat
```

---

## 📋 **ALL AVAILABLE COMPONENTS**

### **🎮 Master Launcher (Recommended)**
- **File**: `0_MASTER_LAUNCHER.bat`
- **Description**: Interactive menu to run any component
- **Usage**: Double-click and select from menu

### **1. 📥 Consolidado Downloader**
- **File**: `1_run_consolidado_downloader.bat`
- **Script**: `portable_app/src/download_consolidado.py`
- **Purpose**: Download latest Consolidado.json from AWS S3
- **Output**: `portable_app/data/Consolidado.json`
- **When to run**: When you need fresh data from the server

### **2. ⚙️ Data Processor**
- **File**: `2_run_data_processor.bat`
- **Script**: `portable_app/src/unified_consolidado_processor.py`
- **Purpose**: Process JSON data into optimized SQLite database
- **Input**: `portable_app/data/Consolidado.json`
- **Output**: `portable_app/data/processed_consolidado.db`
- **When to run**: After downloading new data or when database is missing

### **3. 🧠 VIN Trainer**
- **File**: `3_run_vin_trainer.bat`
- **Script**: `portable_app/src/train_vin_predictor.py`
- **Purpose**: Train machine learning models for VIN prediction
- **Input**: `portable_app/data/processed_consolidado.db`
- **Output**: VIN models in `portable_app/models/`
- **When to run**: When you want to retrain VIN prediction models

### **4. 🎯 SKU Trainer (Frequency Model)**
- **File**: `4_run_sku_trainer.bat`
- **Script**: `scripts/04_train_sku_model.py`
- **Purpose**: Build frequency lookup for SKU prediction (no PyTorch/NumPy)
- **Input**: `Source_Files/processed_consolidado.db`
- **Output**: SKU lookup in `models/sku/`
- **When to run**: After processing data or when lookup needs refresh

### **5. 🖥️ SKU Predictor (Main Application)**
- **File**: `run_sku_predictor.bat`
- **Script**: `portable_app/main_portable.py` → `portable_app/src/main_app.py`
- **Purpose**: Main GUI application for SKU and VIN predictions
- **Requirements**: All models and database must exist
- **When to run**: For daily operations and predictions

---

## 🔧 **SETUP AND TESTING**

### **⚙️ Environment Setup**
- **File**: `setup_portable_environment.bat`
- **Purpose**: Install required Python packages
- **When to run**: First time setup or when packages are missing

### **🧪 Test Mode**
- **File**: `test_sku_predictor.bat`
- **Purpose**: Run minimal test to verify everything works
- **When to run**: To troubleshoot issues or verify installation

---

## 📊 **TYPICAL WORKFLOW**

### **🆕 First Time Setup:**
1. Run `setup_portable_environment.bat` (install packages)
2. Run `1_run_consolidado_downloader.bat` (get data)
3. Run `2_run_data_processor.bat` (process data)
4. Run `3_run_vin_trainer.bat` (train VIN models)
5. Run `4_run_sku_trainer.bat` (train SKU models)
6. Run `run_sku_predictor.bat` (use the application)

### **🔄 Regular Usage:**
- Just run `run_sku_predictor.bat` for daily operations
- Occasionally run downloader + processor for fresh data
- Retrain models when needed for better accuracy

### **🆘 Troubleshooting:**
1. Run `test_sku_predictor.bat` to verify basic functionality
2. Check `portable_app/logs/` for error messages
3. Ensure all data files exist in `portable_app/data/`
4. Verify models exist in `portable_app/models/`

---

## 📁 **FILE LOCATIONS**

### **📊 Data Files** (`portable_app/data/`)
- `Consolidado.json` - Raw data from server
- `processed_consolidado.db` - Processed SQLite database
- `Maestro.xlsx` - Master reference file
- `Text_Processing_Rules.xlsx` - Text processing rules

### **🧠 Model Files** (`models/`)
- `vin/*.joblib` - VIN prediction encoders and models
- `sku/*.joblib` - SKU frequency lookup model
- (No PyTorch/NumPy required in client build)

### **📝 Log Files** (`portable_app/logs/`)
- Application logs and error messages

---

## ⚡ **PERFORMANCE TIPS**

1. **First run takes longer** - Models and database are being optimized
2. **Subsequent runs are faster** - Cached optimizations are used
3. **Close other applications** - For better performance during training
4. **SSD recommended** - Faster database operations

---

## 🆘 **COMMON ISSUES**

### **"Python not found"**
- Run `setup_portable_environment.bat` first

### **"Data files missing"**
- Run the downloader and processor scripts first

### **"Models not found"**
- Run the trainer scripts to create models

### **GUI doesn't appear**
- Check if another instance is running
- Run test mode to verify basic functionality

---

## 🎉 **SUCCESS INDICATORS**

✅ **Application is working when:**
- GUI opens without errors
- Models load successfully (check console output)
- Database queries work (test with a prediction)
- All components show green checkmarks in logs

**Enjoy using Fixacar SKU Predictor v3.0! 🚗**
