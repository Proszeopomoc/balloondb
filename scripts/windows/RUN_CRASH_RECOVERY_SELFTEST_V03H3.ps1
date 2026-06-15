
param([string]$Root = "C:\BalloonOperator")
$ErrorActionPreference = "Stop"
Set-Location $Root
$env:PYTHONPATH = $Root
$env:PYTHONIOENCODING = "utf-8"

py -m py_compile ".\balloondb_core\crash_recovery_v03h3.py"
if ($LASTEXITCODE -ne 0) { throw "V03H3_CRASH_RECOVERY_COMPILE_FAILED" }

py -m py_compile ".\balloondb_core\selftest\run_selftest_v03h3.py"
if ($LASTEXITCODE -ne 0) { throw "V03H3_SELFTEST_COMPILE_FAILED" }

py ".\balloondb_core\selftest\run_selftest_v03h3.py"
if ($LASTEXITCODE -ne 0) { throw "V03H3_SELFTEST_FAILED" }

Write-Host "PASS_RUN_CRASH_RECOVERY_SELFTEST_V03H3" -ForegroundColor Green
