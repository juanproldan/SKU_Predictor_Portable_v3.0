@echo off
setlocal enableextensions enabledelayedexpansion

REM Orchestrates steps 1–4 in sequence.
REM Runs from repo root or Fixacar_SKU_Predictor folder; adjusts CWD accordingly.

pushd "%~dp0"

REM If this script is launched from repo root, descend into Fixacar_SKU_Predictor
if exist "0_install_packages.bat" (
  set BASE_DIR=%cd%
) else if exist "Fixacar_SKU_Predictor\0_install_packages.bat" (
  cd /d "Fixacar_SKU_Predictor"
  set BASE_DIR=%cd%
) else (
  echo [ERROR] Could not locate Fixacar_SKU_Predictor folder.>&2
  popd
  exit /b 1
)

set LOGDIR=%BASE_DIR%\logs
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HH-mm-ss"') do set RUNSTAMP=%%i
set MASTER_LOG=%LOGDIR%\run_all_%RUNSTAMP%.log

REM Display header and also log to file
(echo =============================================
 echo Starting 1_run_all.bat at %DATE% %TIME%
 echo BASE_DIR=%BASE_DIR%
 echo =============================================) > "%MASTER_LOG%"

echo =============================================
echo Starting 1_run_all.bat at %DATE% %TIME%
echo BASE_DIR=%BASE_DIR%
echo =============================================

REM Skip pauses inside step scripts
set SKIP_PAUSE=1

set STEP_OK=1

call :run_step "1_run_consolidado_downloader.bat" || set STEP_OK=0
if %STEP_OK%==0 goto :fail

call :run_step "2_run_data_processor.bat" || set STEP_OK=0
if %STEP_OK%==0 goto :fail

call :run_step "3_run_vin_trainer.bat" || set STEP_OK=0
if %STEP_OK%==0 goto :fail

call :run_step "4_run_sku_trainer.bat" || set STEP_OK=0
if %STEP_OK%==0 goto :fail

(echo [OK] All steps completed successfully.)>> "%MASTER_LOG%"
echo [OK] All steps completed successfully.
goto :end

:run_step
set STEP=%~1
echo.
echo --- Running %STEP% ---
(echo. & echo --- Running %STEP% ---)>> "%MASTER_LOG%"
if not exist "%BASE_DIR%\%STEP%" (
  echo [ERROR] Missing %STEP% in %BASE_DIR%
  (echo [ERROR] Missing %STEP% in %BASE_DIR%)>> "%MASTER_LOG%"
  exit /b 1
)
REM Run step without redirect so console shows progress; steps themselves log.
call "%BASE_DIR%\%STEP%"
set ERR=%ERRORLEVEL%
if not "%ERR%"=="0" (
  echo [ERROR] %STEP% failed with code %ERR%.
  (echo [ERROR] %STEP% failed with code %ERR%.)>> "%MASTER_LOG%"
  exit /b %ERR%
) else (
  echo [OK] %STEP% finished.
  (echo [OK] %STEP% finished.)>> "%MASTER_LOG%"
)
exit /b 0

:fail
echo [FAIL] Pipeline aborted. See log: %MASTER_LOG%
(echo [FAIL] Pipeline aborted.)>> "%MASTER_LOG%"
exit /b 1

:end
popd
endlocal

