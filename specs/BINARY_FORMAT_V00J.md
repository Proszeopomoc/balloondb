# BalloonDB Binary Format V00J

V00J introduces the first explicit binary database core for BalloonDB.

## Scope

- `.bseed` binary seed records
- `.bbridge` binary bridge records
- `.bwal` binary write-ahead log
- `.bdbm` manifest
- CRC32 payload corruption detection
- deterministic record id from SHA-256 payload hash
- write/read/verify/corrupt-detect selftest

## File header

Each binary file starts with a 64-byte header:

| Field | Size | Description |
|---|---:|---|
| magic | 8 | file magic, e.g. `BSEEDJ00` |
| version | 2 | binary format version |
| kind | 2 | seed / bridge / wal kind id |
| header_size | 4 | currently 64 |
| created_ms | 8 | Unix time in milliseconds |
| record_count | 8 | number of records |
| reserved | 32 | reserved zero bytes |

## Record header

Each record starts with a 24-byte header:

| Field | Size | Description |
|---|---:|---|
| record_id | 8 | first 8 bytes of SHA-256 payload hash, little-endian |
| payload_len | 4 | payload byte length |
| crc32 | 4 | CRC32 of payload bytes |
| flags | 4 | reserved flags |
| reserved | 4 | reserved |

## Payload

V00J payloads are canonical UTF-8 JSON bytes stored inside a binary envelope. This is intentional for this layer: the durable file structure is binary, while payload schema can still evolve safely.

Future versions may replace JSON payload bytes with fixed-layout binary payloads for hot-path runtime.

## Selftest

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\RUN_BINARY_FORMAT_SELFTEST_V00J.ps1"
```

Expected:

```text
PASS_BALLOONDB_BINARY_FORMAT_V00J
```
