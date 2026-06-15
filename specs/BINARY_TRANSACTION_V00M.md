# BalloonDB Binary Transaction and Atomic Commit V00M

V00M adds a versioned binary commit protocol.

## Files

- `versions/<version_id>/snapshot.bseed`
- `versions/<version_id>/snapshot.bbridge`
- `versions/<version_id>/snapshot.bindex`
- `versions/<version_id>/snapshot.bwal`
- `versions/<version_id>/snapshot.bdbm`
- `versions/<version_id>/SNAPSHOT_COMPLETE`
- `CURRENT`

## Commit rule

A version is not live until `CURRENT` is atomically replaced.

## Recovery rule

Recovery first validates `CURRENT`. If current points to a corrupt or incomplete version, recovery scans versions and falls back to the newest complete checksum-valid snapshot.

## Validation

The V00M selftest checks:

1. commit v1
2. stage v2 without pointer and verify v1 remains current
3. commit v2
4. corrupt v2
5. recover to previous complete valid v1

Expected marker:

```text
PASS_BALLOONDB_BINARY_TRANSACTION_ATOMIC_COMMIT_V00M
```
