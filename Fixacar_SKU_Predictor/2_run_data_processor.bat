@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Always run from the directory of this script
pushd "%~dp0"

set "LOGSDIR=logs"
if not exist "%LOGSDIR%" mkdir "%LOGSDIR%"
set "LOGFILE=%LOGSDIR%\02_unified_consolidado_processor.log"


echo ========================================
echo STEP 2: PROCESS CONSOLIDADO (Unified Processor)
echo ========================================

echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python not found in PATH. Please install Python or open a terminal where python is available.
  echo Tip: Run 0_install_packages.bat first.
  pause
  popd
  exit /b 1
)

python portable_app\src\unified_consolidado_processor.py %* > "%LOGFILE%" 2>&1
set "ERR=%ERRORLEVEL%"
type "%LOGFILE%"
if not "%ERR%"=="0" (
  echo [ERROR] Processing failed. See log above.
  pause
  popd
  exit /b %ERR%
)

echo [OK] Processing complete.
pause
popd
exit /b 0

