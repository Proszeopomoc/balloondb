# BalloonDB V00O3A Strict V00J Byte Contract

V00O3A hardens V00O3 into a true drop-in contract.

Rules:

- Rust does not serialize JSON.
- Python canonicalizes payload objects with `sort_keys=True`, `separators=(",", ":")`, and `ensure_ascii=False`.
- Rust receives canonical payload bytes and only performs V00J framing.
- `Python bytes == Rust bytes` is required with fixed `created_ms`.
- Golden vectors for unicode, float `1.0`, nested key order, booleans, and null are part of the gate.
- BRS1 remains legacy/lab, not the main BalloonDB storage format.
- Product gate runs the strict Rust/Python V00J golden-vector test and fails closed.

Stable tag target: `v0.0.12-rust-dropin-v00j-format`.
