param(
  [string]$RepoRoot = "C:\BalloonDB_REPO_STAGING"
)
$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path $RepoRoot).Path
$PyRoot = Join-Path $RepoRoot "python_ref"
if (-not (Test-Path (Join-Path $PyRoot "balloondb_core"))) { throw "Missing python_ref\balloondb_core under $RepoRoot" }

$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONPATH = $PyRoot
$env:BALLOONDB_ROOT = $PyRoot
Set-Location $PyRoot

$py = $null
foreach ($c in @("py", "python")) {
  try {
    $v = & $c --version 2>&1
    if ($LASTEXITCODE -eq 0 -and "$v" -match "Python 3") { $py = $c; break }
  } catch {}
}
if (-not $py) { throw "Python 3 not found." }

& $py -m py_compile `
  ".\balloondb_core\bql_error_contract.py" `
  ".\balloondb_core\bql_contract_runner.py" `
  ".\balloondb_core\selftest\run_bql_compat_target_v03h4b.py"
if ($LASTEXITCODE -ne 0) { throw "V03H4B_PY_COMPILE_FAILED" }

& $py -m balloondb_core.selftest.run_bql_compat_target_v03h4b
if ($LASTEXITCODE -ne 0) { throw "V03H4B_TARGET_STATE_BQL_COMPAT_FAILED" }

Write-Host "PASS_RUN_BQL_COMPAT_TARGET_V03H4B" -ForegroundColor Green
