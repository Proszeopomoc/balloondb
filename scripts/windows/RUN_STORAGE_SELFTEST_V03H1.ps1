param([string]$RepoRoot = "")

if (-not $RepoRoot) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

$env:PYTHONPATH = Join-Path $RepoRoot "python_ref"
python -m balloondb_core.selftest.run_selftest_v03h1
if ($LASTEXITCODE -ne 0) {
  throw "V03H1_STORAGE_SELFTEST_FAILED"
}
