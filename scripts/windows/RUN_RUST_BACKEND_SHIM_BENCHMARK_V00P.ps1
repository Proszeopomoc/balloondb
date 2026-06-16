param(
  [switch]$InstallMaturin
)
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..")
Set-Location $RepoRoot

$env:PYTHONPATH = (Join-Path $RepoRoot "python_ref") + [System.IO.Path]::PathSeparator + $env:PYTHONPATH

$RustSelftest = Join-Path $RepoRoot "scripts\windows\RUN_RUST_CORE_PYO3_SELFTEST_V00O.ps1"
if (-not (Test-Path $RustSelftest)) { throw "RUST_CORE_SELFTEST_RUNNER_NOT_FOUND" }
$Args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $RustSelftest)
if ($InstallMaturin) { $Args += "-InstallMaturin" }
& powershell.exe @Args
if ($LASTEXITCODE -ne 0) { throw "RUST_CORE_PYO3_SELFTEST_FAILED_FOR_V00P" }

$SelftestPath = Join-Path $RepoRoot "python_ref\balloondb_core\selftest\run_rust_backend_shim_benchmark_v00p.py"
if (-not (Test-Path $SelftestPath)) { throw "V00P_SELFTEST_MODULE_FILE_MISSING: $SelftestPath" }
python $SelftestPath
if ($LASTEXITCODE -ne 0) { throw "RUST_BACKEND_SHIM_BENCHMARK_V00P_FAILED" }

Write-Host "PASS_BALLOONDB_RUST_BACKEND_SHIM_BENCHMARK_V00P"
