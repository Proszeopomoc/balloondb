param(
  [string]$RepoRoot = "",
  [switch]$InstallMaturin
)

$ErrorActionPreference = "Stop"

if (-not $RepoRoot) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

cd $RepoRoot
$env:PYTHONPATH = Join-Path $RepoRoot "python_ref"

$cargo = Get-Command cargo -ErrorAction SilentlyContinue
if (-not $cargo) { throw "RUST_CARGO_NOT_FOUND_INSTALL_RUSTUP_FIRST" }

python -m maturin --version *> $null
if ($LASTEXITCODE -ne 0) {
  if ($InstallMaturin) {
    python -m pip install --user maturin
  } else {
    throw "MATURIN_NOT_FOUND_RUN_WITH_-InstallMaturin_OR_INSTALL: python -m pip install --user maturin"
  }
}

$Crate = Join-Path $RepoRoot "rust\balloondb_core_rs"
$WheelDir = Join-Path $RepoRoot "audit\v00o\wheels"
New-Item -ItemType Directory -Force -Path $WheelDir | Out-Null

python -m maturin build --manifest-path (Join-Path $Crate "Cargo.toml") --release --out $WheelDir
if ($LASTEXITCODE -ne 0) { throw "MATURIN_BUILD_FAILED" }

$Wheel = Get-ChildItem $WheelDir -Filter "*.whl" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $Wheel) { throw "NO_WHEEL_BUILT" }

python -m pip install --user --force-reinstall --no-deps $Wheel.FullName
if ($LASTEXITCODE -ne 0) { throw "PIP_INSTALL_RUST_WHEEL_FAILED" }

python -m balloondb_core.selftest.run_rust_core_pyo3_v00o
if ($LASTEXITCODE -ne 0) { throw "RUST_CORE_PYO3_SELFTEST_V00O_FAILED" }

Write-Host "PASS_BALLOONDB_RUST_CORE_PYO3_V00O"
