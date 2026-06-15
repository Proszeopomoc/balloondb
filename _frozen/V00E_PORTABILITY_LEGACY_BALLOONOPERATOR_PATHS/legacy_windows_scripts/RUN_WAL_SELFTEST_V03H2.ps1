
param([string]$Root = "C:\BalloonOperator")
$ErrorActionPreference = "Stop"
Set-Location $Root
$env:PYTHONPATH = $Root
$env:PYTHONIOENCODING = "utf-8"

py -m py_compile ".\balloondb_core\wal_v03h2.py"
if ($LASTEXITCODE -ne 0) { throw "V03H2_WAL_COMPILE_FAILED" }

py -m py_compile ".\balloondb_core\selftest\run_selftest_v03h2.py"
if ($LASTEXITCODE -ne 0) { throw "V03H2_SELFTEST_COMPILE_FAILED" }

py ".\balloondb_core\selftest\run_selftest_v03h2.py"
if ($LASTEXITCODE -ne 0) { throw "V03H2_SELFTEST_FAILED" }

Write-Host "PASS_RUN_WAL_SELFTEST_V03H2" -ForegroundColor Green
