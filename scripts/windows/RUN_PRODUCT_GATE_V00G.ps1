param([string]$RepoRoot = "")

if (-not $RepoRoot) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

cd $RepoRoot
$ErrorActionPreference = "Stop"

$RequiredFiles = @(
  "README.md",
  "docs\QUICKSTART.md",
  "specs\API_SPEC.md",
  "specs\TRUST_STATE_SPEC.md",
  "specs\PRODUCT_ARCHITECTURE.md",
  "specs\FORMAT_SPEC.md",
  "specs\BINARY_FORMAT_V00J.md",
  "scripts\windows\RUN_STORAGE_SELFTEST_V03H1.ps1",
  "scripts\windows\RUN_WAL_SELFTEST_V03H2.ps1",
  "scripts\windows\RUN_CRASH_RECOVERY_SELFTEST_V03H3.ps1",
  "scripts\windows\RUN_BQL_COMPAT_TARGET_V03H4B.ps1",
  "scripts\windows\RUN_BINARY_FORMAT_SELFTEST_V00J.ps1",
  "scripts\windows\RUN_BINARY_TRANSACTION_SELFTEST_V00M.ps1"
)

$Missing = @()
foreach ($f in $RequiredFiles) {
  if (-not (Test-Path (Join-Path $RepoRoot $f))) { $Missing += $f }
}

$ActiveHits = Get-ChildItem ".\python_ref", ".\scripts" -Recurse -File |
  Where-Object {
    $_.FullName -notmatch "\\_frozen\\" -and
    $_.FullName -notmatch "\\audit\\" -and
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
  ".\scripts\windows\RUN_STORAGE_SELFTEST_V03H1.ps1",
  ".\scripts\windows\RUN_WAL_SELFTEST_V03H2.ps1",
  ".\scripts\windows\RUN_CRASH_RECOVERY_SELFTEST_V03H3.ps1",
  ".\scripts\windows\RUN_BQL_COMPAT_TARGET_V03H4B.ps1",
  ".\scripts\windows\RUN_BINARY_FORMAT_SELFTEST_V00J.ps1",
  ".\scripts\windows\RUN_BINARY_INDEX_QUERY_SELFTEST_V00K.ps1",
  ".\scripts\windows\RUN_BINARY_COMPACTION_SNAPSHOT_SELFTEST_V00L.ps1",
  ".\scripts\windows\RUN_BINARY_TRANSACTION_SELFTEST_V00M.ps1"
)

$RunnerFailures = @()
foreach ($r in $RunnerFiles) {
  if (Test-Path $r) {
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File $r
    if ($LASTEXITCODE -ne 0) {
      $RunnerFailures += $r
    }
  }
}

$Summary = [PSCustomObject]@{
  status = "PASS_BALLOONDB_PRODUCT_GATE_V00M1"
  repo_root = $RepoRoot
  missing_required_files = $Missing.Count
  active_root_hits = $ActiveHits.Count
  tracked_generated_count = $TrackedGenerated.Count
  python_compile_fail = $CompileFail.Count
  runner_failures = $RunnerFailures.Count
}

if ($Missing.Count -ne 0 -or $ActiveHits.Count -ne 0 -or $TrackedGenerated.Count -ne 0 -or $CompileFail.Count -ne 0 -or $RunnerFailures.Count -ne 0) {
  $Summary.status = "NO_GO_BALLOONDB_PRODUCT_GATE_V00M1"
  $Summary | ConvertTo-Json -Depth 5
  throw "NO_GO_BALLOONDB_PRODUCT_GATE_V00M1"
}

$Summary | ConvertTo-Json -Depth 5
Write-Host "PASS_BALLOONDB_PRODUCT_GATE_V00M1"
