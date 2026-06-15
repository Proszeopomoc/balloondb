param(
  [string]$Root = "C:\BalloonOperator",
  [string]$MemoryRoot = "C:\BalloonOperator\memory\balloon_memory.balloondb"
)
$ErrorActionPreference = "Stop"
Set-Location $Root
$env:PYTHONPATH = $Root
$env:PYTHONIOENCODING = "utf-8"

py -m py_compile `
  ".\balloondb_core\bql_daemon.py" `
  ".\balloondb_core\bql_daemon_client.py" `
  ".\balloondb_core\selftest\run_selftest_v03g4.py"

if ($LASTEXITCODE -ne 0) { throw "V03G4_PY_COMPILE_FAILED" }

$code = @"
import sys, json
sys.path.insert(0, r"$Root")
from balloondb_core.selftest.run_selftest_v03g4 import run_selftest
result = run_selftest(r"$MemoryRoot")
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result.get("status") == "PASS_V03G4_BQL_HOT_DAEMON_SELFTEST" else 8)
"@

New-Item -ItemType Directory -Force ".\06_EVIDENCE\BALLOONDB_BQL_CORE" | Out-Null
$tmp = ".\06_EVIDENCE\BALLOONDB_BQL_CORE\run_v03g4_selftest_tmp.py"
[System.IO.File]::WriteAllText((Resolve-Path ".\06_EVIDENCE\BALLOONDB_BQL_CORE").Path + "\run_v03g4_selftest_tmp.py", $code, (New-Object System.Text.UTF8Encoding($false)))

py $tmp

if ($LASTEXITCODE -ne 0) { throw "V03G4_SELFTEST_FAILED" }

Write-Host "PASS_RUN_BQL_SELFTEST_V03G4" -ForegroundColor Green
