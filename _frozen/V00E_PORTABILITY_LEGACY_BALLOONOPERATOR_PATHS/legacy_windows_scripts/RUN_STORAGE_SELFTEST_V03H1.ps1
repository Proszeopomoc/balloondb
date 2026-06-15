
param([string]$Root = "C:\BalloonOperator")
$ErrorActionPreference = "Stop"
Set-Location $Root
$env:PYTHONPATH = $Root
$env:PYTHONIOENCODING = "utf-8"

py -m py_compile ".\balloondb_core\storage_format_v03h1.py"
if ($LASTEXITCODE -ne 0) { throw "V03H1_STORAGE_COMPILE_FAILED" }

py -m py_compile ".\balloondb_core\selftest\run_selftest_v03h1.py"
if ($LASTEXITCODE -ne 0) { throw "V03H1_SELFTEST_COMPILE_FAILED" }

py ".\balloondb_core\selftest\run_selftest_v03h1.py"
if ($LASTEXITCODE -ne 0) { throw "V03H1_SELFTEST_FAILED" }

Write-Host "PASS_RUN_STORAGE_SELFTEST_V03H1" -ForegroundColor Green
