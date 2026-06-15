param([string]$Root="C:\BalloonOperator",[string]$MemoryRoot="C:\BalloonOperator\memory\balloon_memory.balloondb")
$ErrorActionPreference="Stop"; $env:PYTHONIOENCODING="utf-8"; Set-Location $Root
$py=$null; foreach($c in @("py","python")){try{$v=& $c --version 2>&1; if($LASTEXITCODE -eq 0 -and "$v" -match "Python 3"){$py=$c; break}}catch{}}
if(-not $py){throw "Python 3 not found."}
& $py -m py_compile ".\balloondb_core\bql_memory_reader.py" ".\balloondb_core\bql_executor.py" ".\balloondb_core\cli.py" ".\balloondb_core\selftest\run_selftest_v03g1.py"
if($LASTEXITCODE -ne 0){throw "V03G1_PY_COMPILE_FAILED"}
& $py -m balloondb_core.cli selftest-v03g1 --memory-root $MemoryRoot
if($LASTEXITCODE -ne 0){throw "V03G1_SELFTEST_FAILED"}
Write-Host "PASS_RUN_BQL_SELFTEST_V03G1" -ForegroundColor Green
