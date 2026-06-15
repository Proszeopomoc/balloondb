
param([string]$Root = "C:\BalloonOperator")
$ErrorActionPreference = "Stop"
Set-Location $Root
$env:PYTHONPATH = $Root
$env:PYTHONIOENCODING = "utf-8"

py -m py_compile ".\balloondb_core\selftest\run_core_regression_gate_v03h4.py"
if ($LASTEXITCODE -ne 0) { throw "V03H4_CORE_REGRESSION_GATE_COMPILE_FAILED" }

py ".\balloondb_core\selftest\run_core_regression_gate_v03h4.py"
if ($LASTEXITCODE -ne 0) { throw "V03H4_CORE_REGRESSION_GATE_FAILED" }

Write-Host "PASS_RUN_BALLOONDB_V03H4_CORE_REGRESSION_RELEASE_GATE" -ForegroundColor Green
