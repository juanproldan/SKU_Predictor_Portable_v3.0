@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Always run from the directory of this script
pushd "%~dp0"

set "LOGSDIR=logs"
if not exist "%LOGSDIR%" mkdir "%LOGSDIR%"
set "LOGFILE=%LOGSDIR%\01_sync_consolidado.log"


echo ========================================
echo STEP 1: SYNC CONSOLIDADO (Source_Files)
echo ========================================

echo Checking Python (Windows Launcher)...
py -3.11 --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3.11 not found via 'py -3.11'. Please install Python 3.11.
  echo Tip: Run 0_install_packages.bat first.
  pause
  popd
  exit /b 1
)

REM Stream output live to console AND save to log via PowerShell Tee-Object
powershell -NoProfile -ExecutionPolicy Bypass -Command "py -3.11 scripts\01_sync_consolidado.py --download %* 2^>^&1 ^| Tee-Object -FilePath '%LOGFILE%'"
set "ERR=%ERRORLEVEL%"
if not "%ERR%"=="0" (
  echo [ERROR] Sync failed. See log above.
  pause
  popd
  exit /b %ERR%
)

echo [OK] Source_Files ready.
pause
popd
exit /b 0

