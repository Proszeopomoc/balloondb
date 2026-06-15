param(
  [Parameter(Mandatory=$true)][string]$QueryFile,
  [string]$Root = "C:\BalloonOperator",
  [string]$MemoryRoot = "C:\BalloonOperator\memory\balloon_memory.balloondb",
  [int]$Port = 8765,
  [int]$MaxResults = 50,
  [string]$OutJson = ""
)
$ErrorActionPreference = "Stop"
Set-Location $Root
$env:PYTHONPATH = $Root
$env:PYTHONIOENCODING = "utf-8"

py -m balloondb_core.bql_daemon_client `
  --cmd query `
  --host 127.0.0.1 `
  --port $Port `
  --query-file $QueryFile `
  --memory-root $MemoryRoot `
  --max-results $MaxResults `
  --out-json $OutJson
