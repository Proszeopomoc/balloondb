param([string]$RepoRoot = "")

if (-not $RepoRoot) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

cd $RepoRoot
$env:PYTHONPATH = Join-Path $RepoRoot "python_ref"

python -m balloondb_core.selftest.run_binary_format_v00j
if ($LASTEXITCODE -ne 0) {
  throw "V00J_BINARY_FORMAT_SELFTEST_FAILED"
}
