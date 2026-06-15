param([string]$RepoRoot = "")

if (-not $RepoRoot) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

$env:PYTHONPATH = Join-Path $RepoRoot "python_ref"
python -m balloondb_core.selftest.run_selftest_v03h3
if ($LASTEXITCODE -ne 0) {
  throw "V03H3_CRASH_RECOVERY_SELFTEST_FAILED"
}
