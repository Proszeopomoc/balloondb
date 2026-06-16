# BalloonDB Binary Compaction and Snapshot V00L

V00L adds snapshot compaction over V00J/V00K binary storage.

## Scope

- replay `.bwal` delta entries over base `.bseed` and `.bbridge`
- compact current state into snapshot `.bseed` and `.bbridge`
- build `.bindex` for the snapshot
- write `.bdbm` snapshot manifest
- write `SNAPSHOT_COMPLETE` marker after successful manifest write
- recover from last complete snapshot
- detect corrupt snapshot data through CRC validation

## Supported WAL operations in V00L

```text
UPSERT_SEED
UPSERT_BRIDGE
DELETE_SEED
DELETE_BRIDGE
```

## Selftest

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\RUN_BINARY_COMPACTION_SNAPSHOT_SELFTEST_V00L.ps1"
```

Expected:

```text
PASS_BALLOONDB_BINARY_COMPACTION_SNAPSHOT_V00L
```

## Position in roadmap

V00J introduced binary records and WAL. V00K introduced binary indexing and lookup. V00L adds compaction and snapshot recovery so the database can checkpoint state and recover from a compact binary snapshot.
