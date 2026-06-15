param(
  [string]$Root = "C:\BalloonOperator",
  [string]$MemoryRoot = "C:\BalloonOperator\memory\balloon_memory.balloondb",
  [int]$Port = 8765
)
$ErrorActionPreference = "Stop"
Set-Location $Root
$env:PYTHONPATH = $Root
$env:PYTHONIOENCODING = "utf-8"

New-Item -ItemType Directory -Force ".\06_EVIDENCE\BALLOONDB_BQL_CORE" | Out-Null

$py = "py"
try { & $py --version | Out-Null } catch { $py = "python" }

$logOut = ".\06_EVIDENCE\BALLOONDB_BQL_CORE\V03G4_DAEMON.stdout.log"
$logErr = ".\06_EVIDENCE\BALLOONDB_BQL_CORE\V03G4_DAEMON.stderr.log"
$pidfile = ".\06_EVIDENCE\BALLOONDB_BQL_CORE\V03G4_DAEMON.pid"

if (Test-Path $pidfile) {
  try {
    $oldPid = [int](Get-Content $pidfile -Raw)
    if (Get-Process -Id $oldPid -ErrorAction SilentlyContinue) {
      Stop-Process -Id $oldPid -Force
    }
  } catch {}
  Remove-Item $pidfile -Force -ErrorAction SilentlyContinue
}

$p = Start-Process `
  -FilePath $py `
  -ArgumentList @("-m","balloondb_core.bql_daemon","--host","127.0.0.1","--port","$Port","--memory-root",$MemoryRoot) `
  -WorkingDirectory $Root `
  -RedirectStandardOutput $logOut `
  -RedirectStandardError $logErr `
  -PassThru `
  -WindowStyle Hidden

Set-Content $pidfile $p.Id -Encoding ASCII
Start-Sleep -Milliseconds 700

$report = @{
  status = "PASS_V03G4_DAEMON_START_REQUESTED"
  version = "V03G5D_REPAIRED_START_SCRIPT"
  pid = $p.Id
  port = $Port
  stdout = $logOut
  stderr = $logErr
  fix = "separate_stdout_stderr_redirect"
  ts = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
}
$report | ConvertTo-Json -Depth 6

Write-Host "PASS_V03G4_DAEMON_START_REQUESTED PID=$($p.Id) PORT=$Port" -ForegroundColor Green
