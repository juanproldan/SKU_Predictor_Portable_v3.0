@echo off
setlocal EnableExtensions EnableDelayedExpansion

pushd "%~dp0"

set "LOGSDIR=logs"
if not exist "%LOGSDIR%" mkdir "%LOGSDIR%"
set "LOGFILE=%LOGSDIR%\04_train_sku_model.log"


echo ========================================
echo STEP 4: TRAIN SKU MODEL (Universal)
echo ========================================

echo Checking Python (Windows Launcher)...
py -3.11 --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3.11 not found via 'py -3.11'. Please install Python 3.11.
  pause
  popd
  exit /b 1
)

py -3.11 scripts\04_train_sku_model.py %* > "%LOGFILE%" 2>&1
set "ERR=%ERRORLEVEL%"
type "%LOGFILE%"
if not "%ERR%"=="0" (
  echo [ERROR] SKU training failed. See log above.
  pause
  popd
  exit /b %ERR%
)

echo [OK] SKU model trained.
pause
popd
exit /b 0

