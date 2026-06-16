# BalloonDB Binary Index and Query V00K

V00K adds the first binary index layer over V00J `.bseed` and `.bbridge` files.

## Scope

- `.bindex` binary index envelope
- index over `.bseed` and `.bbridge` records
- lookup by `record_id`
- lookup by `type`
- lookup by `trust_state`
- lookup by `relation`
- lookup by logical id
- minimal binary query contract
- index CRC corruption detection

## Query subset

V00K supports a deliberately small binary index query subset:

```text
FIND record_id=<integer>
FIND type=<value>
FIND trust_state=<value>
FIND relation=<value>
FIND logical_id=<value>
```

Unsupported SQL/BQL-like syntax must be rejected with a stable error status.

## Selftest

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\RUN_BINARY_INDEX_QUERY_SELFTEST_V00K.ps1"
```

Expected:

```text
PASS_BALLOONDB_BINARY_INDEX_QUERY_V00K
```

## Position in roadmap

V00J proves binary record storage and WAL. V00K adds binary indexing and query lookup, making BalloonDB closer to a usable database core.
