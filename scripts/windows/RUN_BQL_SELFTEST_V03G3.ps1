param(
  [string]$Root = "C:\BalloonOperator",
  [string]$MemoryRoot = "C:\BalloonOperator\memory\balloon_memory.balloondb"
)
$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONPATH = $Root
Set-Location $Root

$py = $null
foreach ($c in @("py","python")) {
  try {
    $v = & $c --version 2>&1
    if ($LASTEXITCODE -eq 0 -and "$v" -match "Python 3") { $py = $c; break }
  } catch {}
}
if (-not $py) { throw "Python 3 not found." }

& $py -m py_compile `
  ".\balloondb_core\bql_error_contract.py" `
  ".\balloondb_core\bql_contract_runner.py" `
  ".\balloondb_core\selftest\run_selftest_v03g3.py"

if ($LASTEXITCODE -ne 0) { throw "V03G3_PY_COMPILE_FAILED" }

New-Item -ItemType Directory -Force ".\06_EVIDENCE\BALLOONDB_BQL_CORE" | Out-Null

$code = @"
import sys
sys.path.insert(0, r"$Root")
from balloondb_core.selftest.run_selftest_v03g3 import run_selftest
import json
result = run_selftest(r"$MemoryRoot")
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result.get("status") == "PASS_V03G3_BQL_SELFTEST" else 7)
"@

$tmp = ".\06_EVIDENCE\BALLOONDB_BQL_CORE\run_v03g3_selftest_tmp.py"
[System.IO.File]::WriteAllText((Resolve-Path ".\06_EVIDENCE\BALLOONDB_BQL_CORE").Path + "\run_v03g3_selftest_tmp.py", $code, (New-Object System.Text.UTF8Encoding($false)))

& $py $tmp

if ($LASTEXITCODE -ne 0) { throw "V03G3_SELFTEST_FAILED" }

Write-Host "PASS_RUN_BQL_SELFTEST_V03G3" -ForegroundColor Green
