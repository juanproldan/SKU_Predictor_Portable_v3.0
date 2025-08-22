@echo off
setlocal EnableExtensions EnableDelayedExpansion

pushd "%~dp0"

set "LOGSDIR=logs"
if not exist "%LOGSDIR%" mkdir "%LOGSDIR%"
set "LOGFILE=%LOGSDIR%\03_train_vin_model.log"


echo ========================================
echo STEP 3: TRAIN VIN MODEL (Universal)
echo ========================================

echo Checking Python (Windows Launcher)...
py -3.11 --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3.11 not found via 'py -3.11'. Please install Python 3.11.
  if not defined SKIP_PAUSE pause
  popd
  exit /b 1
)

py -3.11 scripts\03_train_vin_model.py %* > "%LOGFILE%" 2>&1
set "ERR=%ERRORLEVEL%"
type "%LOGFILE%"
if not "%ERR%"=="0" (
  echo [ERROR] VIN training failed. See log above.
  if not defined SKIP_PAUSE pause
  popd
  exit /b %ERR%
)

echo [OK] VIN models trained.
if not defined SKIP_PAUSE pause
popd
exit /b 0

