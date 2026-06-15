$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot
$env:PYTHONPATH = (Join-Path $RepoRoot "python_ref")

$RequiredFiles = @(
  "README.md",
  "CHANGELOG.md",
  "LICENSE",
  "AGENT_CONTRACT.md",
  "specs\API_SPEC.md",
  "specs\TRUST_STATE_SPEC.md",
  "specs\PRODUCT_ARCHITECTURE.md",
  "specs\FORMAT_SPEC.md",
  "specs\BINARY_FORMAT_V00J.md",
  "specs\RUST_CORE_PYO3_V00O.md",
  "specs\RUST_DROPIN_V00J_COMPAT_V00O3.md",
  "pyproject.toml",
  "rust\balloondb_core_rs\Cargo.toml",
  "rust\balloondb_core_rs\Cargo.lock",
  "rust\balloondb_core_rs\src\lib.rs",
  "python_ref\balloondb_core\rust_core_v00o.py",
  "python_ref\balloondb_core\selftest\run_rust_core_pyo3_v00o.py",
  "scripts\windows\RUN_STORAGE_SELFTEST_V03H1.ps1",
  "scripts\windows\RUN_WAL_SELFTEST_V03H2.ps1",
  "scripts\windows\RUN_CRASH_RECOVERY_SELFTEST_V03H3.ps1",
  "scripts\windows\RUN_BQL_COMPAT_TARGET_V03H4B.ps1",
  "scripts\windows\RUN_BINARY_FORMAT_SELFTEST_V00J.ps1",
  "scripts\windows\RUN_BINARY_TRANSACTION_SELFTEST_V00M.ps1",
  "scripts\windows\RUN_RUST_CORE_PYO3_SELFTEST_V00O.ps1"
)

$Missing = @()
foreach ($f in $RequiredFiles) {
  if (-not (Test-Path (Join-Path $RepoRoot $f))) { $Missing += $f }
}

$ActiveHits = Get-ChildItem ".\python_ref", ".\scripts", ".\rust" -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object {
    $_.FullName -notmatch "\\_frozen\\" -and
    $_.FullName -notmatch "\\audit\\" -and
    $_.FullName -notmatch "\\target\\" -and
    $_.FullName -notmatch "\\\.git\\" -and
    $_.Extension -notin @(".pyc", ".pyo")
  } |
  Select-String -Pattern "C:\\BalloonDB_REPO_STAGING|C:\\BalloonOperator" -ErrorAction SilentlyContinue

$TrackedGenerated = git ls-files |
  Where-Object {
    ($_ -match '^audit/v03h4b/') -or
    ($_ -match '^audit/v00j/') -or
    ($_ -match '^audit/v00k/') -or
    ($_ -match '^audit/v00l/') -or
    ($_ -match '^audit/v00m/') -or
    ($_ -match '^audit/v00m1/') -or
    ($_ -match '^audit/v00o/') -or
    ($_ -match '^audit/v00o3/') -or
    ($_ -match '^rust/balloondb_core_rs/target/') -or
    ($_ -match '^python_ref/balloondb_core/data/' -and $_ -notmatch '\.gitkeep$') -or
    ($_ -match '^python_ref/balloondb_core/reports/' -and $_ -notmatch '\.gitkeep$') -or
    ($_ -match '^balloondb_core/')
  }

$CompileFail = @()
$PyFiles = Get-ChildItem ".\python_ref" -Recurse -File -Filter "*.py"
foreach ($f in $PyFiles) {
  python -m py_compile $f.FullName
  if ($LASTEXITCODE -ne 0) { $CompileFail += $f.FullName }
}

$RunnerFiles = @(
  @{ Path = ".\scripts\windows\RUN_STORAGE_SELFTEST_V03H1.ps1"; Args = @() },
  @{ Path = ".\scripts\windows\RUN_WAL_SELFTEST_V03H2.ps1"; Args = @() },
  @{ Path = ".\scripts\windows\RUN_CRASH_RECOVERY_SELFTEST_V03H3.ps1"; Args = @() },
  @{ Path = ".\scripts\windows\RUN_BQL_COMPAT_TARGET_V03H4B.ps1"; Args = @() },
  @{ Path = ".\scripts\windows\RUN_BINARY_FORMAT_SELFTEST_V00J.ps1"; Args = @() },
  @{ Path = ".\scripts\windows\RUN_BINARY_INDEX_QUERY_SELFTEST_V00K.ps1"; Args = @() },
  @{ Path = ".\scripts\windows\RUN_BINARY_COMPACTION_SNAPSHOT_SELFTEST_V00L.ps1"; Args = @() },
  @{ Path = ".\scripts\windows\RUN_BINARY_TRANSACTION_SELFTEST_V00M.ps1"; Args = @() },
  @{ Path = ".\scripts\windows\RUN_RUST_CORE_PYO3_SELFTEST_V00O.ps1"; Args = @("-InstallMaturin") }
)

$RunnerFailures = @()
foreach ($r in $RunnerFiles) {
  if (Test-Path $r.Path) {
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File $r.Path @($r.Args)
    if ($LASTEXITCODE -ne 0) {
      $RunnerFailures += $r.Path
    }
  }
}

$Summary = [PSCustomObject]@{
  status = "PASS_BALLOONDB_PRODUCT_GATE_V00O3"
  repo_root = $RepoRoot
  missing_required_files = $Missing.Count
  active_root_hits = $ActiveHits.Count
  tracked_generated_count = $TrackedGenerated.Count
  python_compile_fail = $CompileFail.Count
  runner_failures = $RunnerFailures.Count
}

if ($Missing.Count -ne 0 -or $ActiveHits.Count -ne 0 -or $TrackedGenerated.Count -ne 0 -or $CompileFail.Count -ne 0 -or $RunnerFailures.Count -ne 0) {
  $Summary.status = "NO_GO_BALLOONDB_PRODUCT_GATE_V00O3"
  $Summary | ConvertTo-Json -Depth 5
  throw "NO_GO_BALLOONDB_PRODUCT_GATE_V00O3"
}

$Summary | ConvertTo-Json -Depth 5
Write-Host "PASS_BALLOONDB_PRODUCT_GATE_V00O3"