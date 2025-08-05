@echo off
echo ========================================
echo 5. Fixacar SKU Predictor v3.0 (Main App)
echo ========================================
echo.

REM Check if portable Python exists
if not exist "portable_python\python_env\Scripts\python.exe" (
    echo ERROR: Portable Python not found!
    echo.
    echo Please run setup_portable_environment.bat first
    echo to set up the Python environment.
    echo.
    pause
    exit /b 1
)

REM Set Python path
set PYTHON_PATH=%CD%\portable_python\python_env\Scripts\python.exe
set PYTHONPATH=%CD%\portable_app\src;%PYTHONPATH%

echo Starting SKU Predictor...
echo Python: %PYTHON_PATH%
echo Working Directory: %CD%\portable_app
echo.

REM Change to portable_app directory and run the application
cd portable_app
"%PYTHON_PATH%" main_portable.py --gui

echo.
echo Application closed.
pause
