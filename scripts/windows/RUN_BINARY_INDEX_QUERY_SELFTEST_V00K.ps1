param([string]$RepoRoot = "")

if (-not $RepoRoot) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

cd $RepoRoot
$env:PYTHONPATH = Join-Path $RepoRoot "python_ref"

python -m balloondb_core.selftest.run_binary_index_v00k
if ($LASTEXITCODE -ne 0) {
  throw "V00K_BINARY_INDEX_QUERY_SELFTEST_FAILED"
}
