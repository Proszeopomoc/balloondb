param([string]$RepoRoot = "")

if (-not $RepoRoot) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

cd $RepoRoot
$env:PYTHONPATH = Join-Path $RepoRoot "python_ref"

python -m balloondb_core.selftest.run_binary_snapshot_v00l
if ($LASTEXITCODE -ne 0) {
  throw "V00L_BINARY_COMPACTION_SNAPSHOT_SELFTEST_FAILED"
}
