param([string]$Root="C:\BalloonOperator",[string]$MemoryRoot="C:\BalloonOperator\memory\balloon_memory.balloondb",[string]$Query="",[string]$QueryFile="",[int]$MaxResults=50)
$ErrorActionPreference="Stop"; $env:PYTHONIOENCODING="utf-8"; Set-Location $Root
$py=$null; foreach($c in @("py","python")){try{$v=& $c --version 2>&1; if($LASTEXITCODE -eq 0 -and "$v" -match "Python 3"){$py=$c; break}}catch{}}
if(-not $py){throw "Python 3 not found."}
$argsList=@("-m","balloondb_core.cli","query","--memory-root",$MemoryRoot,"--max-results","$MaxResults")
if($QueryFile -ne ""){$argsList+=@("--query-file",$QueryFile)} elseif($Query -ne ""){$argsList+=@("--query",$Query)} else {throw "Query or QueryFile required."}
& $py @argsList
if($LASTEXITCODE -ne 0){throw "V03G1_BQL_QUERY_FAILED"}
