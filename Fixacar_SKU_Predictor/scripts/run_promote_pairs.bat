@echo off
setlocal

set SCRIPT_DIR=%~dp0
pushd "%SCRIPT_DIR%"

REM Use Python 3.11 to run the safe runner that waits for Excel to close and reopens the workbook
py -3.11 "%SCRIPT_DIR%run_promote_pairs.py"

popd
endlocal

