# BalloonDB V00O3 Rust Drop-in V00J Format Compatibility

V00O3 resolves the architecture decision after V00O:

- BRS1 is not promoted to the main database format.
- The main storage format remains the Python V00J `.bseed/.bbridge/.bwal` layout.
- Rust now implements V00J-compatible record and file encoding/decoding.
- Python can use Rust when the extension is available and fall back to Python V00J otherwise.
- Product gate now runs the Rust/PyO3 selftest.
- `pyproject.toml` wires maturin so `pip install .` can build the extension.
- Rust/TOML files are written without BOM.

## Tested roundtrips

1. Python writes V00J `.bseed` -> Rust reads it.
2. Rust writes V00J `.bseed` -> Python reads it.
3. Rust record id equals Python V00J record id.
4. Rust detects V00J CRC corruption.
5. Python fallback path still works.

## Non-goal

V00O3 does not revive V00N page-store. Page-store remains paused until the Rust/Python format boundary is stable.