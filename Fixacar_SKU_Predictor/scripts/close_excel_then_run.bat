@echo off
setlocal

set ROOT=%~dp0..\
set XLSX=%ROOT%Source_Files\Text_Processing_Rules.xlsx
set PROMO_PY=%ROOT%scripts\run_promote_pairs.py
set PROCESSOR=%ROOT%2_run_data_processor.bat
for %%F in ("%XLSX%") do set FILENAME=%%~nxF
set LOCK=%ROOT%Source_Files\~$%FILENAME%

REM 1) Save and close the target workbook via COM to avoid recovery prompts
powershell -NoProfile -Command "$path=[System.IO.Path]::GetFullPath('%XLSX%'); try { $excel=[Runtime.InteropServices.Marshal]::GetActiveObject('Excel.Application') } catch {}; if ($excel) { $target=$null; foreach ($wb in @($excel.Workbooks)) { if ($wb.FullName -eq $path) { $target=$wb; break } } if ($target) { $target.Save(); $target.Close($true); if ($excel.Workbooks.Count -eq 0) { $excel.Quit() } } }"

REM 2) Wait a moment for file handles to release
ping -n 2 127.0.0.1 >NUL

REM 2b) If lock still present, force-close Excel to release it
if exist "%LOCK%" (
  powershell -NoProfile -Command "$p=Get-Process EXCEL -ErrorAction SilentlyContinue; if ($p) { $p | ForEach-Object { $_.CloseMainWindow() | Out-Null; Start-Sleep -Milliseconds 500; if (!$_.HasExited) { $_.Kill() } } }"
  ping -n 2 127.0.0.1 >NUL
)

REM 3) Run promotions (will not reopen Excel)
py -3.11 "%PROMO_PY%"
if errorlevel 1 (
  echo Promotion step failed. Aborting.
  goto :EOF
)

REM 4) Run data processor as requested
call "%PROCESSOR%"

REM 5) Reopen the workbook
start "" "%XLSX%"

endlocal

