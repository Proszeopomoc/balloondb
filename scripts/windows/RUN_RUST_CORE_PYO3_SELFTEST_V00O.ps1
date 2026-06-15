param(
  [switch]$InstallMaturin
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot
$env:PYTHONPATH = (Join-Path $RepoRoot "python_ref")
$env:BALLOONDB_REQUIRE_RUST_V00J = "1"

if ($InstallMaturin) {
  python -m pip install --user maturin | Out-Host
}

python -m maturin --version *> $null
if ($LASTEXITCODE -ne 0) { throw "MATURIN_NOT_AVAILABLE" }

cargo --version *> $null
if ($LASTEXITCODE -ne 0) { throw "CARGO_NOT_AVAILABLE" }

rustc --version *> $null
if ($LASTEXITCODE -ne 0) { throw "RUSTC_NOT_AVAILABLE" }

$WheelDir = Join-Path $RepoRoot "audit\v00o\wheels"
New-Item -ItemType Directory -Force -Path $WheelDir | Out-Null

python -m maturin build --manifest-path ".\rust\balloondb_core_rs\Cargo.toml" --release --out $WheelDir
if ($LASTEXITCODE -ne 0) { throw "MATURIN_BUILD_FAILED" }

$Wheel = Get-ChildItem $WheelDir -Filter "balloondb_core_rs-*.whl" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $Wheel) { throw "RUST_WHEEL_NOT_FOUND" }

python -m pip install --force-reinstall $Wheel.FullName | Out-Host
if ($LASTEXITCODE -ne 0) { throw "RUST_WHEEL_INSTALL_FAILED" }

python -m balloondb_core.selftest.run_rust_core_pyo3_v00o
if ($LASTEXITCODE -ne 0) { throw "RUST_CORE_PYO3_SELFTEST_FAILED" }

python -m balloondb_core.selftest.run_v00j_rust_compat_v00o3
if ($LASTEXITCODE -ne 0) { throw "STRICT_V00J_GOLDEN_GATE_FAILED" }
