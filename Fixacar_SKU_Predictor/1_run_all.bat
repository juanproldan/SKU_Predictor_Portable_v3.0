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
set RUNSTAMP=%DATE:~10,4%-%DATE:~4,2%-%DATE:~7,2%_%TIME:~0,2%-%TIME:~3,2%-%TIME:~6,2%
set RUNSTAMP=%RUNSTAMP: =0%
set MASTER_LOG=%LOGDIR%\run_all_%RUNSTAMP%.log

echo ============================================= | tee -a "%MASTER_LOG%"
echo Starting 1_run_all.bat at %DATE% %TIME%       | tee -a "%MASTER_LOG%"
echo BASE_DIR=%BASE_DIR%                            | tee -a "%MASTER_LOG%"
echo ============================================= | tee -a "%MASTER_LOG%"

set STEP_OK=1

call :run_step "1_run_consolidado_downloader.bat" || set STEP_OK=0
if %STEP_OK%==0 goto :fail

call :run_step "2_run_data_processor.bat" || set STEP_OK=0
if %STEP_OK%==0 goto :fail

call :run_step "3_run_vin_trainer.bat" || set STEP_OK=0
if %STEP_OK%==0 goto :fail

call :run_step "4_run_sku_trainer.bat" || set STEP_OK=0
if %STEP_OK%==0 goto :fail

echo [OK] All steps completed successfully. | tee -a "%MASTER_LOG%"
goto :eof

:run_step
set STEP=%~1
echo. | tee -a "%MASTER_LOG%"
echo --- Running %STEP% --- | tee -a "%MASTER_LOG%"
if not exist "%BASE_DIR%\%STEP%" (
  echo [ERROR] Missing %STEP% in %BASE_DIR% | tee -a "%MASTER_LOG%"
  exit /b 1
)
call "%BASE_DIR%\%STEP%" >> "%MASTER_LOG%" 2>&1
if errorlevel 1 (
  echo [ERROR] %STEP% failed. See log: %MASTER_LOG% | tee -a "%MASTER_LOG%"
  exit /b 1
) else (
  echo [OK] %STEP% finished. | tee -a "%MASTER_LOG%"
)
exit /b 0

:fail
echo [FAIL] Pipeline aborted. See log: %MASTER_LOG% | tee -a "%MASTER_LOG%"
exit /b 1

:end
popd
endlocal

