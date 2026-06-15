## v0.0.8-binary-compaction-snapshot

- Added binary snapshot compaction from base files plus WAL.
- Added snapshot manifest and SNAPSHOT_COMPLETE marker.
- Added recovery from complete binary snapshot.
- Added corrupt snapshot detection.

## v0.0.7-binary-index-query

- Added .bindex binary index envelope.
- Added record id, type, trust state, relation, and logical id lookup.
- Added minimal binary query selftest.
- Added corrupt index detection.

## v0.0.5-binary-db-core

- Added V00J binary .bseed, .bbridge, .bwal, and .bdbm manifest core.
- Added CRC corruption detection selftest.
- Added binary format specification.

# Changelog

## v0.0.4-agpl-license

- Added AGPL-3.0-only license.
- Added SECURITY.md.
- Added CONTRIBUTING.md.
- Added NOTICE.md.
- Updated product gate to require public-readiness files.

## v0.0.3-product-gate

- Added product documentation.
- Added product gate script.
- Verified product gate from clean clone.

## v0.0.2-repo-hygiene

- Removed generated test outputs from Git.
- Confirmed generated outputs remain local and ignored.

## v0.0.1-root-portable

- Fixed H4B fresh-clone root binding.
- Verified root-portable BQL gate.

## v0.0.0-staging-v00e

- Initial clean BalloonDB staging baseline.
- Separated core repository from BalloonOperator workspace.




## v0.0.9-binary-transaction-atomic-commit

- Added V00M binary transaction and atomic commit selftest.
- Added versioned snapshots with CURRENT pointer recovery.


## v0.0.10-binary-transaction-gate-fixed

- Fixes V00M binary transaction selftest.
- Fixes product gate so failed subrunners fail the gate.
- Adds clean transaction recovery report for versioned snapshots and fallback recovery.
