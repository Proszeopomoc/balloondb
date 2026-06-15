param(
  [Parameter(Mandatory=$true)][string]$QueryFile,
  [string]$Root = "C:\BalloonOperator",
  [string]$MemoryRoot = "C:\BalloonOperator\memory\balloon_memory.balloondb",
  [int]$MaxResults = 50,
  [string]$OutJson = "",
  [string]$OutHtml = ""
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

New-Item -ItemType Directory -Force ".\06_EVIDENCE\BALLOONDB_BQL_CORE" | Out-Null

$resolvedQuery = (Resolve-Path $QueryFile).Path

$code = @"
import sys, pathlib, json
sys.path.insert(0, r"$Root")
from balloondb_core.bql_contract_runner import run_query_contract
from balloondb_core.bql_error_contract import write_json, write_html_report

query = pathlib.Path(r"$resolvedQuery").read_text(encoding="utf-8-sig")
env = run_query_contract(query, memory_root=r"$MemoryRoot", max_results=$MaxResults)
print(json.dumps(env, ensure_ascii=False, indent=2))

out_json = r"$OutJson"
if out_json:
    write_json(out_json, env)

out_html = r"$OutHtml"
if out_html:
    cases = [{"name":"query_contract", "pass": env.get("ok", False), "expect":"ok query envelope", "envelope": env}]
    write_html_report(out_html, "BalloonDB V03G3 query contract report", cases)

raise SystemExit(0 if env.get("ok") else 4)
"@

$tmp = ".\06_EVIDENCE\BALLOONDB_BQL_CORE\run_v03g3_query_contract_tmp.py"
[System.IO.File]::WriteAllText((Resolve-Path ".\06_EVIDENCE\BALLOONDB_BQL_CORE").Path + "\run_v03g3_query_contract_tmp.py", $code, (New-Object System.Text.UTF8Encoding($false)))

& $py $tmp
