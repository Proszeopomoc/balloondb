param(
  [string]$Root = "C:\BalloonOperator"
)
$ErrorActionPreference = "Stop"
Set-Location $Root

$pidfile = ".\06_EVIDENCE\BALLOONDB_BQL_CORE\V03G4_DAEMON.pid"

if (Test-Path $pidfile) {
  $daemonPidText = Get-Content $pidfile -Raw
  $daemonPid = [int]($daemonPidText.Trim())

  if (Get-Process -Id $daemonPid -ErrorAction SilentlyContinue) {
    Stop-Process -Id $daemonPid -Force
  }

  Remove-Item $pidfile -Force -ErrorAction SilentlyContinue
}

$report = @{
  status = "PASS_V03G4_DAEMON_STOPPED"
  version = "V03G5D1_REPAIRED_STOP_SCRIPT"
  fix = "avoid_reserved_PID_variable_use_daemonPid"
  ts = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
}
$report | ConvertTo-Json -Depth 6

Write-Host "PASS_V03G4_DAEMON_STOPPED" -ForegroundColor Green
