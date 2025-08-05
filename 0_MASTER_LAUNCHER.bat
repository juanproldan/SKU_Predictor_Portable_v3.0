@echo off
title Fixacar SKU Predictor v3.0 - Master Launcher
color 0A

:MAIN_MENU
cls
echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║              FIXACAR SKU PREDICTOR v3.0                     ║
echo  ║                  PORTABLE PYTHON EDITION                    ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.
echo  🚗 Welcome to the Fixacar SKU Predictor v3.0!
echo.
echo  📋 AVAILABLE COMPONENTS:
echo.
echo  [1] 📥 Consolidado Downloader    - Download latest data from S3
echo  [2] ⚙️  Data Processor           - Process JSON to optimized database
echo  [3] 🧠 VIN Trainer              - Train VIN prediction models
echo  [4] 🎯 SKU Trainer              - Train SKU prediction models
echo  [5] 🖥️  SKU Predictor (Main App) - Run the main application
echo.
echo  [T] 🧪 Test Mode                - Run minimal test version
echo  [S] ⚙️  Setup Environment       - Install Python packages
echo.
echo  [Q] ❌ Quit
echo.
set /p choice="  👉 Select an option (1-5, T, S, Q): "

if /i "%choice%"=="1" goto RUN_DOWNLOADER
if /i "%choice%"=="2" goto RUN_PROCESSOR
if /i "%choice%"=="3" goto RUN_VIN_TRAINER
if /i "%choice%"=="4" goto RUN_SKU_TRAINER
if /i "%choice%"=="5" goto RUN_MAIN_APP
if /i "%choice%"=="T" goto RUN_TEST
if /i "%choice%"=="S" goto RUN_SETUP
if /i "%choice%"=="Q" goto QUIT

echo.
echo  ❌ Invalid option. Please try again.
timeout /t 2 >nul
goto MAIN_MENU

:RUN_DOWNLOADER
cls
echo  🚀 Launching Consolidado Downloader...
call 1_run_consolidado_downloader.bat
goto RETURN_TO_MENU

:RUN_PROCESSOR
cls
echo  🚀 Launching Data Processor...
call 2_run_data_processor.bat
goto RETURN_TO_MENU

:RUN_VIN_TRAINER
cls
echo  🚀 Launching VIN Trainer...
call 3_run_vin_trainer.bat
goto RETURN_TO_MENU

:RUN_SKU_TRAINER
cls
echo  🚀 Launching SKU Trainer...
call 4_run_sku_trainer.bat
goto RETURN_TO_MENU

:RUN_MAIN_APP
cls
echo  🚀 Launching Main SKU Predictor Application...
call run_sku_predictor.bat
goto RETURN_TO_MENU

:RUN_TEST
cls
echo  🚀 Launching Test Mode...
call test_sku_predictor.bat
goto RETURN_TO_MENU

:RUN_SETUP
cls
echo  🚀 Launching Environment Setup...
call setup_portable_environment.bat
goto RETURN_TO_MENU

:RETURN_TO_MENU
echo.
echo  ✅ Component finished. Press any key to return to main menu...
pause >nul
goto MAIN_MENU

:QUIT
cls
echo.
echo  👋 Thank you for using Fixacar SKU Predictor v3.0!
echo  🚗 Drive safe!
echo.
timeout /t 2 >nul
exit
