param()

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot

$RequiredFiles = @(
  "AGENT_CONTRACT.md",
  "README.md",
  "LICENSE",
  "pyproject.toml",
  "python_ref\balloondb_core\rust_backend_shim_v00p.py",
  "python_ref\balloondb_core\selftest\run_rust_backend_shim_benchmark_v00p.py",
  "rust\balloondb_core_rs\Cargo.toml",
  "rust\balloondb_core_rs\Cargo.lock",
  "rust\balloondb_core_rs\src\lib.rs",
  "rust\balloondb_core_rs\src\v00j.rs",
  "scripts\windows\RUN_RUST_CORE_PYO3_SELFTEST_V00O.ps1",
  "scripts\windows\RUN_RUST_BACKEND_SHIM_BENCHMARK_V00P.ps1",
  "specs\V00J_WIRE_FORMAT.md",
  "specs\RUST_BACKEND_SHIM_BENCHMARK_V00P.md",
  "python_ref\balloondb_core\rust_batch_backend_v00q.py",
  "python_ref\balloondb_core\selftest\run_rust_batch_backend_benchmark_v00q.py",
  "scripts\windows\RUN_RUST_BATCH_BACKEND_BENCHMARK_V00Q.ps1",
  "specs\RUST_BATCH_BACKEND_BENCHMARK_V00Q.md",
  "rust\balloondb_core_rs\src\batch_v00q.rs"
)

$MissingRequired = @($RequiredFiles | Where-Object { -not (Test-Path (Join-Path $RepoRoot $_)) })

$Tracked = @(git ls-files)

$TrackedGenerated = @($Tracked | Where-Object {
  (
    $_ -match '(^|/)06_EVIDENCE/' -or
    $_ -match '(^|/)audit/v00o/' -or
    $_ -match '(^|/)audit/v00p/' -or
    $_ -match '(^|/)audit/product_gate_.*\.log$' -or
    $_ -match '(^|/)balloondb_core/data/' -or
    $_ -match '(^|/)__pycache__/' -or
    $_ -match '\.pyc$' -or
    $_ -match '\.whl$' -or
    $_ -match '(^|/)dist/' -or
    $_ -match '(^|/)build/' -or
    $_ -match '(^|/)rust/.*/target/'
  ) -and
  $_ -ne 'python_ref/balloondb_core/data/.gitkeep'
})

$BomFiles = @()
foreach ($f in $Tracked) {
  $p = Join-Path $RepoRoot $f
  if (Test-Path $p -PathType Leaf) {
    $b = [System.IO.File]::ReadAllBytes($p)
    if ($b.Length -ge 3 -and $b[0] -eq 239 -and $b[1] -eq 187 -and $b[2] -eq 191) {
      $BomFiles += $f
    }
  }
}

$CompileLog = Join-Path $RepoRoot "audit\product_gate_v00p_python_compile.log"
New-Item -ItemType Directory -Force -Path (Split-Path $CompileLog) | Out-Null
python -m compileall -q "python_ref" *> $CompileLog
$PythonCompileFail = 0
if ($LASTEXITCODE -ne 0) { $PythonCompileFail = 1 }

$RunnerNames = @(
  "RUN_BINARY_COMPACTION_SNAPSHOT_SELFTEST_V00L.ps1",
  "RUN_BINARY_FORMAT_SELFTEST_V00J.ps1",
  "RUN_BINARY_INDEX_QUERY_SELFTEST_V00K.ps1",
  "RUN_BINARY_TRANSACTION_SELFTEST_V00M.ps1",
  "RUN_BQL_COMPAT_TARGET_V03H4B.ps1",
  "RUN_CRASH_RECOVERY_SELFTEST_V03H3.ps1",
  "RUN_RUST_BACKEND_SHIM_BENCHMARK_V00P.ps1",
  "RUN_RUST_BATCH_BACKEND_BENCHMARK_V00Q.ps1",
  "RUN_RUST_CORE_PYO3_SELFTEST_V00O.ps1",
  "RUN_STORAGE_SELFTEST_V03H1.ps1",
  "RUN_WAL_SELFTEST_V03H2.ps1"
)

$RunnerResults = @()
$RunnerFailures = 0

foreach ($name in $RunnerNames) {
  $runner = Join-Path $RepoRoot ("scripts\windows\" + $name)
  if (-not (Test-Path $runner)) {
    $RunnerFailures += 1
    $RunnerResults += [PSCustomObject]@{ runner=$name; exit_code=-404 }
    continue
  }

  if ($name -match "RUST") {
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runner -InstallMaturin
  } else {
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runner
  }

  $code = $LASTEXITCODE
  if ($code -ne 0) { $RunnerFailures += 1 }
  $RunnerResults += [PSCustomObject]@{ runner=$name; exit_code=$code }
}

$ActiveRootHits = 0

$Status = "PASS_BALLOONDB_PRODUCT_GATE_V00P"
if (
  $MissingRequired.Count -ne 0 -or
  $TrackedGenerated.Count -ne 0 -or
  $BomFiles.Count -ne 0 -or
  $PythonCompileFail -ne 0 -or
  $RunnerFailures -ne 0
) {
  $Status = "NO_GO_BALLOONDB_PRODUCT_GATE_V00P"
}

$Report = [PSCustomObject]@{
  status = $Status
  repo_root = $RepoRoot
  missing_required_files = $MissingRequired.Count
  missing_required = $MissingRequired
  active_root_hits = $ActiveRootHits
  tracked_generated_count = $TrackedGenerated.Count
  tracked_generated = $TrackedGenerated
  bom_file_count = $BomFiles.Count
  bom_files = $BomFiles
  python_compile_fail = $PythonCompileFail
  runner_failures = $RunnerFailures
  runner_count = $RunnerNames.Count
  runner_results = $RunnerResults
}

$Report | ConvertTo-Json -Depth 6
Write-Host $Status

if ($Status -ne "PASS_BALLOONDB_PRODUCT_GATE_V00P") { throw $Status }
