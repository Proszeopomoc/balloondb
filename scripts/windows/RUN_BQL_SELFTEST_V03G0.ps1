param(
  [string]$Root = "C:\BalloonOperator"
)
$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
Set-Location $Root

$py = $null
foreach ($c in @("py","python")) {
  try {
    $v = & $c --version 2>&1
    if ($LASTEXITCODE -eq 0 -and "$v" -match "Python 3") { $py = $c; break }
  } catch {}
}
if (-not $py) { throw "Python 3 not found." }

& $py -m py_compile `
  ".\balloondb_core\bql_ast.py" `
  ".\balloondb_core\bql_parser.py" `
  ".\balloondb_core\bql_planner.py" `
  ".\balloondb_core\role_map_loader.py" `
  ".\balloondb_core\cli.py" `
  ".\balloondb_core\selftest\run_selftest.py"

if ($LASTEXITCODE -ne 0) { throw "V03G0_PY_COMPILE_FAILED" }

& $py -m balloondb_core.cli selftest

if ($LASTEXITCODE -ne 0) { throw "V03G0_SELFTEST_FAILED" }

Write-Host "PASS_RUN_BQL_SELFTEST_V03G0" -ForegroundColor Green
