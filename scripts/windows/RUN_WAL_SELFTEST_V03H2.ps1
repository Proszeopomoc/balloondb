param([string]$RepoRoot = "")

if (-not $RepoRoot) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

$env:PYTHONPATH = Join-Path $RepoRoot "python_ref"
python -m balloondb_core.selftest.run_selftest_v03h2
if ($LASTEXITCODE -ne 0) {
  throw "V03H2_WAL_SELFTEST_FAILED"
}
