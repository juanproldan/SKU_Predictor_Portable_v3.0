@echo off
echo ========================================
echo Fixacar SKU Predictor v3.0 Setup
echo ========================================
echo.

REM Check if portable_python directory exists
if not exist "portable_python" (
    echo Creating portable_python directory...
    mkdir portable_python
)

echo.
echo SETUP INSTRUCTIONS:
echo.
echo 1. Download Python 3.11 Portable from:
echo    https://www.python.org/downloads/windows/
echo    OR
echo    https://github.com/winpython/winpython/releases
echo.
echo 2. Extract Python to: portable_python\python_env\
echo.
echo 3. Run this script again to install packages
echo.

REM Check if Python is installed
if exist "portable_python\python_env\Scripts\python.exe" (
    echo Python found! Installing required packages...
    echo.
    
    REM Set Python path
    set PYTHON_PATH=%CD%\portable_python\python_env\Scripts\python.exe
    set PIP_PATH=%CD%\portable_python\python_env\Scripts\pip.exe
    
    echo Installing core packages...
    "%PIP_PATH%" install numpy pandas scikit-learn
    
    echo Installing ML packages...
    "%PIP_PATH%" install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    
    echo Installing NLP packages...
    "%PIP_PATH%" install spacy
    "%PYTHON_PATH%" -m spacy download es_core_news_sm
    
    echo Installing utility packages...
    "%PIP_PATH%" install openpyxl xlrd fuzzywuzzy python-levenshtein
    
    echo.
    echo ========================================
    echo Setup Complete!
    echo ========================================
    echo.
    echo You can now run the application with:
    echo run_sku_predictor.bat
    echo.
    
) else (
    echo.
    echo Python not found in portable_python\python_env\
    echo Please follow the instructions above.
    echo.
)

pause
