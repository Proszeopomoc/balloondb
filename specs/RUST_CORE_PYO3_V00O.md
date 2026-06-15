# Rust Core + PyO3 Bridge V00O

V00O introduces the first Rust/PyO3 experimental binary core for BalloonDB.

## Scope

- Rust crate: `rust/balloondb_core_rs`
- Python extension module: `balloondb_core_rs`
- Python bridge: `balloondb_core.rust_core_v00o`
- Selftest: `balloondb_core.selftest.run_rust_core_pyo3_v00o`

## Current record format

The Rust record format is intentionally minimal and independent from the existing Python binary V00J/V00M files.

Header fields:

- magic: `BRS1`
- version: `1`
- kind: `u8`
- trust: `u8`
- logical_id length: `u16`
- payload length: `u32`
- CRC32 of body
- SHA-256 record id

Body:

- logical id bytes
- payload bytes

## Guarantees in V00O

- deterministic encoding
- deterministic record id
- CRC corruption detection
- Python binding through PyO3 0.22 Bound API

## Not yet included

- page store
- transaction engine
- binary index integration
- Rust replacement of Python product gate

V00O is a Rust-core bridge milestone, not yet a full Rust storage engine replacement.
