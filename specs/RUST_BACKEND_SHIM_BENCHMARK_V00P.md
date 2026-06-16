# BalloonDB V00P — Rust backend shim and benchmark

V00P connects the strict V00J Rust/Python byte contract to the Python reference layer.

Rules:

- Rust is used only when `balloondb_core_rs` is importable and exposes the V00J API.
- Python remains the canonical JSON producer.
- Rust receives canonical payload bytes; Rust does not serialize JSON.
- Python fallback must produce byte-identical V00J record bytes.
- Benchmark numbers are reported as evidence, not used as a pass/fail condition.

Acceptance:

- Rust backend available.
- Auto backend selects Rust.
- Forced Python fallback works.
- Rust bytes == Python bytes.
- Fallback bytes == Python bytes.
- Product gate runs this shim/benchmark runner.
