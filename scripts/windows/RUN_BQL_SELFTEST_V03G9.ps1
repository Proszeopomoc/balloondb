$ErrorActionPreference = 'Stop'
cd "C:\BalloonOperator"
$env:PYTHONPATH = "C:\BalloonOperator"
$env:PYTHONIOENCODING = "utf-8"
& py -m balloondb_core.selftest.run_selftest_v03g9
$code = $LASTEXITCODE
exit $code
