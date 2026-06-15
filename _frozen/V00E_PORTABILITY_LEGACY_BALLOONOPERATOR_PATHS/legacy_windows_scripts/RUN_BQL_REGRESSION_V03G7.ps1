Param(
    [string]$OutJson,
    [string]$OutHtml,
    [string]$Layers,
    [int]$TimeoutSec = 1800,
    [switch]$AllowEmpty,
    [switch]$VerboseRunner
)

$ErrorActionPreference = 'Stop'

$Root = 'C:\BalloonOperator'
Set-Location $Root

$env:PYTHONPATH = $Root
$env:PYTHONIOENCODING = 'utf-8'

$VenvPython = Join-Path $Root '.venv\Scripts\python.exe'
if (Test-Path $VenvPython) {
    $PythonExe = $VenvPython
} else {
    $PythonExe = 'python'
}

if ([string]::IsNullOrWhiteSpace($OutJson)) {
    $OutJson = 'C:\BalloonOperator\data\v03g7_bql_regression_report.json'
}

if ([string]::IsNullOrWhiteSpace($OutHtml)) {
    $OutHtml = 'C:\BalloonOperator\reports\v03g7_bql_regression_summary.html'
}

$RunnerArgs = @(
    '-m', 'balloondb_core.selftest.run_selftest_v03g7_all',
    '--scripts-dir', 'C:\BalloonOperator\09_SCRIPTS',
    '--out-json', $OutJson,
    '--out-html', $OutHtml,
    '--timeout', ([string]$TimeoutSec)
)

if (-not [string]::IsNullOrWhiteSpace($Layers)) {
    $RunnerArgs += @('--layers', $Layers)
}

if ($AllowEmpty.IsPresent) {
    $RunnerArgs += '--allow-empty'
}

if ($VerboseRunner.IsPresent) {
    $RunnerArgs += '--verbose'
}

& $PythonExe @RunnerArgs
exit $LASTEXITCODE
