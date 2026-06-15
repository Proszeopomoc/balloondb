$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
Set-Location $Root
$env:PYTHONPATH = $Root
$env:PYTHONIOENCODING = "utf-8"

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
  $Python = $VenvPython
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  $Python = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
  $Python = "py"
} else {
  Write-Error "No Python interpreter found."
  exit 127
}

& $Python "balloondb_core/selftest/run_selftest_v03g8.py"
$Code = $LASTEXITCODE
if ($Code -ne 0) {
  exit $Code
}
exit 0
