$ErrorActionPreference = 'Stop'

# Resolve project root from the script location, not the caller working directory.
$ExpectedRoot = 'C:\BalloonOperator'
$ScriptDir = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($ScriptDir)) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$ResolvedRoot = (Resolve-Path -LiteralPath (Join-Path -Path $ScriptDir -ChildPath '..')).ProviderPath.TrimEnd('\')
$NormalizedExpectedRoot = $ExpectedRoot.TrimEnd('\')

# Reject execution unless the normalized resolved root is exactly C:\BalloonOperator.
if ($ResolvedRoot -ne $NormalizedExpectedRoot) {
    $failure = [ordered]@{
        status = 'FAIL_V03G6_BQL_SELFTEST_WRAPPER_ROOT_GUARD'
        expected_root = $NormalizedExpectedRoot
        resolved_root = $ResolvedRoot
        safety = [ordered]@{
            root_only = $true
            no_network_exposure = $true
            no_retry_loops = $true
            api_spend = $false
        }
    }
    Write-Host ($failure | ConvertTo-Json -Compress)
    exit 91
}

Set-Location -LiteralPath $NormalizedExpectedRoot
$env:PYTHONPATH = $NormalizedExpectedRoot
$env:PYTHONIOENCODING = 'utf-8'

$EvidenceDir = Join-Path -Path $NormalizedExpectedRoot -ChildPath '06_EVIDENCE\BALLOONDB_BQL_CORE'
if (-not (Test-Path -LiteralPath $EvidenceDir)) {
    New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null
}

Write-Host '{"status":"RUNNING_V03G6_BQL_SELFTEST_WRAPPER","feature_id":"V03G6_BQL_TIME_FILTER","python_command":"py -m balloondb_core.selftest.run_selftest_v03g6"}'

& py -m balloondb_core.selftest.run_selftest_v03g6
$PythonExitCode = $LASTEXITCODE

if ($PythonExitCode -eq 0) {
    $summaryStatus = 'PASS_V03G6_BQL_SELFTEST_WRAPPER'
} else {
    $summaryStatus = 'FAIL_V03G6_BQL_SELFTEST_WRAPPER'
}

$summary = [ordered]@{
    status = $summaryStatus
    feature_id = 'V03G6_BQL_TIME_FILTER'
    python_exit_code = $PythonExitCode
    evidence_dir = '06_EVIDENCE\BALLOONDB_BQL_CORE'
    safety = [ordered]@{
        root_only = $true
        no_network_exposure = $true
        no_daemon_start = $true
        no_package_install = $true
        no_retry_loops = $true
        api_spend = $false
    }
}
Write-Host ($summary | ConvertTo-Json -Compress)
exit $PythonExitCode
