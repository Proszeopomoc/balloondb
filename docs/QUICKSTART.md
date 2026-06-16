# BalloonDB Quickstart

## Requirements

- Windows PowerShell
- Python 3.12+
- Git

## Clone

```powershell
git clone https://github.com/Proszeopomoc/balloondb.git C:\BalloonDB
cd C:\BalloonDB
```

## Run product gate

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\RUN_PRODUCT_GATE_V00G.ps1"
```

## Individual gates

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\RUN_STORAGE_SELFTEST_V03H1.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\RUN_WAL_SELFTEST_V03H2.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\RUN_CRASH_RECOVERY_SELFTEST_V03H3.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\RUN_BQL_COMPAT_TARGET_V03H4B.ps1"
```

After tests, Git should remain clean:

```powershell
git status --short
```
