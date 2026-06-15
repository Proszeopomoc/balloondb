
param(
  [string]$Root = "C:\BalloonOperator",
  [switch]$Apply
)
$ErrorActionPreference = "Stop"
Set-Location $Root
$env:PYTHONPATH = $Root
$env:PYTHONIOENCODING = "utf-8"

$argsList = @("-m", "balloondb_core.selftest.bql_compat_fix_v03h4a")
if ($Apply) { $argsList += "--apply" }

py @argsList
