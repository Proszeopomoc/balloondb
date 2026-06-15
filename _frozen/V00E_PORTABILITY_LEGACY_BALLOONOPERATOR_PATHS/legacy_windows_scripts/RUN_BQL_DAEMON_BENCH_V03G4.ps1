param(
  [Parameter(Mandatory=$true)][string]$QueryFile,
  [string]$Root = "C:\BalloonOperator",
  [string]$MemoryRoot = "C:\BalloonOperator\memory\balloon_memory.balloondb",
  [int]$Port = 8765,
  [int]$Repeat = 20
)
$ErrorActionPreference = "Stop"
Set-Location $Root
$env:PYTHONPATH = $Root
$env:PYTHONIOENCODING = "utf-8"

py -m balloondb_core.bql_daemon_client `
  --cmd bench `
  --host 127.0.0.1 `
  --port $Port `
  --query-file $QueryFile `
  --memory-root $MemoryRoot `
  --repeat $Repeat `
  --out-json ".\06_EVIDENCE\BALLOONDB_BQL_CORE\V03G4_DAEMON_BENCHMARK.json"
