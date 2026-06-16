
## V00Q - Rust batch backend benchmark

- Added Rust/PyO3 batch V00J framing benchmark.
- Measures batch sizes 1 / 100 / 1000 / 10000.
- Reports Python framing, Rust batch framing, canonical JSON, and PyO3 crossing baseline.
- Speed is reported but not used as pass/fail.

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

## v0.0.11-rust-core-pyo3

- Added experimental Rust core crate with PyO3 0.22 bindings.
- Added deterministic Rust binary record encode/decode.
- Added CRC corruption detection in Rust selftest.
- Added Python bridge module for Rust extension.

## v0.0.12 - V00O3 Rust drop-in V00J compatibility

- Rust/PyO3 can read/write the existing Python V00J binary format.
- Added Python shim: Rust if available, Python fallback otherwise.
- Added root pyproject.toml for maturin build integration.
- Product gate now runs Rust/PyO3 selftest fail-closed.
- Rust/TOML files written without BOM.

## v0.0.13 - V00O3A Strict Rust drop-in V00J byte contract

- Added V00J wire-format spec and golden vectors.
- Rust exposes v00j_record_id, v00j_encode_record, v00j_write_file, v00j_read_file.
- Product gate runs strict Rust/Python byte-for-byte V00J compatibility test.
- BRS1 remains legacy/lab and is not promoted as main storage format.

## V00P Rust backend shim and benchmark

- Added 
ust_backend_shim_v00p.py.
- Added Rust-vs-Python V00J backend benchmark selftest.
- Product gate now runs V00P runner and reports PASS_BALLOONDB_PRODUCT_GATE_V00P.
