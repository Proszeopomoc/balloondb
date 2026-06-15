param([string]$RepoRoot = "")

if (-not $RepoRoot) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

$env:PYTHONPATH = Join-Path $RepoRoot "python_ref"
Remove-Item Env:\BALLOONDB_ROOT -ErrorAction SilentlyContinue

python -m balloondb_core.selftest.run_bql_compat_target_v03h4b
if ($LASTEXITCODE -ne 0) {
  throw "V03H4B_TARGET_STATE_BQL_COMPAT_FAILED"
}
