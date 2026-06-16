# V00Q Rust batch backend benchmark

V00Q measures where the Rust/PyO3 backend becomes useful.

It does not change the public V00J wire format.

## Contract

Rust still receives canonical payload bytes from Python. Rust does not serialize JSON.

The benchmark compares:

- Python V00J framing for a list of canonical payload bytes.
- Rust V00J batch framing via one PyO3 crossing per batch.
- PyO3 crossing/extraction baseline using a count-only batch function.
- Batch sizes: 1, 100, 1000, 10000.

## Pass/fail

Speed is reported but is not a pass/fail condition.

Pass requires:

- Rust extension available.
- Python bytes equal Rust bytes for every tested batch.
- Auto backend selects Rust when available.
- Explicit Python fallback produces identical bytes.
