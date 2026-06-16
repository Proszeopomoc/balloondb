param(
  [switch]$InstallMaturin
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot

$env:PYTHONPATH = Join-Path $RepoRoot "python_ref"

$RustRunner = Join-Path $RepoRoot "scripts\windows\RUN_RUST_CORE_PYO3_SELFTEST_V00O.ps1"
if ($InstallMaturin) {
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File $RustRunner -InstallMaturin
} else {
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File $RustRunner
}
if ($LASTEXITCODE -ne 0) { throw "RUST_CORE_PYO3_SELFTEST_FAILED_FOR_V00Q" }

python (Join-Path $RepoRoot "python_ref\balloondb_core\selftest\run_rust_batch_backend_benchmark_v00q.py")
if ($LASTEXITCODE -ne 0) { throw "RUST_BATCH_BACKEND_BENCHMARK_V00Q_FAILED" }
