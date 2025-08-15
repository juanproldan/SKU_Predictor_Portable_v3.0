@echo off
setlocal EnableExtensions EnableDelayedExpansion

pushd "%~dp0"

set "LOGSDIR=logs"
if not exist "%LOGSDIR%" mkdir "%LOGSDIR%"
set "LOGFILE=%LOGSDIR%\05_run_predictions.log"

echo ========================================
echo STEP 5: LAUNCH SKU PREDICTOR GUI (Universal)
echo =============================================

echo Checking Python (Windows Launcher)...
py -3.11 --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3.11 not found via 'py -3.11'. Please install Python 3.11.
  pause
  popd
  exit /b 1
)

REM Launch full FixacarApp GUI (Path A)
py -3.11 portable_app\main_portable.py --gui %*
set "ERR=%ERRORLEVEL%"
if not "%ERR%"=="0" (
  echo [ERROR] GUI launch failed.
  pause
  popd
  exit /b %ERR%
)

echo [OK] GUI closed.
pause
popd
exit /b 0
