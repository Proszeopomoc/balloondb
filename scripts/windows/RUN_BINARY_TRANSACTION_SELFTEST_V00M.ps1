param([string]$RepoRoot = "")

if (-not $RepoRoot) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

$env:PYTHONPATH = Join-Path $RepoRoot "python_ref"
python -m balloondb_core.selftest.run_binary_transaction_v00m
if ($LASTEXITCODE -ne 0) {
  throw "V00M_BINARY_TRANSACTION_ATOMIC_COMMIT_FAILED"
}
