@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Always run from the directory of this script
pushd "%~dp0"

set "LOGSDIR=logs"
if not exist "%LOGSDIR%" mkdir "%LOGSDIR%"
set "LOG_PROCESS=%LOGSDIR%\02_unified_consolidado_processor.log"
set "LOG_ABBR=%LOGSDIR%\02_new_abbreviations_pairs.log"


echo ========================================
echo STEP 2: PROCESS CONSOLIDADO (Unified Processor)
echo ========================================

echo Checking Python (Windows Launcher)...
py -3.11 --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3.11 not found via 'py -3.11'. Please install Python 3.11.
  echo Tip: Run 0_install_packages.bat first.
  if not defined SKIP_PAUSE pause
  popd
  exit /b 1
)

REM Run the unified consolidado processor
py -3.11 portable_app\src\unified_consolidado_processor.py %* > "%LOG_PROCESS%" 2>&1
set "ERR=%ERRORLEVEL%"
type "%LOG_PROCESS%"
if not "%ERR%"=="0" (
  echo [ERROR] Processing failed. See log above.
  if not defined SKIP_PAUSE pause
  popd
  exit /b %ERR%
)

echo.
echo ========================================
echo POST-PROCESS: Generate NewAbbreviations suggestions

echo Running generator: scripts\generate_new_abbreviations_pairs.py
py -3.11 scripts\generate_new_abbreviations_pairs.py > "%LOG_ABBR%" 2>&1
set "ERR_ABBR=%ERRORLEVEL%"
type "%LOG_ABBR%"
if not "%ERR_ABBR%"=="0" (
  echo [ERROR] NewAbbreviations generation failed. See log above.
  if not defined SKIP_PAUSE pause
  popd
  exit /b %ERR_ABBR%
)

echo [OK] Processing complete and NewAbbreviations regenerated.
if not defined SKIP_PAUSE pause
popd
exit /b 0

