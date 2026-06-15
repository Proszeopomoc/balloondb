"""Rust/PyO3 bridge for BalloonDB V00O.

This module intentionally fails fast if the Rust extension is not installed.
Use scripts/windows/RUN_RUST_CORE_PYO3_SELFTEST_V00O.ps1 to build and test it.
"""

try:
    import balloondb_core_rs as _rs
except Exception as exc:  # pragma: no cover
    _rs = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


def require_rust():
    if _rs is None:
        raise RuntimeError(f"balloondb_core_rs extension not available: {_IMPORT_ERROR}")
    return _rs


def encode_record(kind: int, trust: int, logical_id: str, payload: bytes) -> bytes:
    return bytes(require_rust().encode_record(kind, trust, logical_id, payload))


def decode_record(data: bytes) -> dict:
    d = require_rust().decode_record(data)
    d["payload"] = bytes(d["payload"])
    return d


def record_id_hex(kind: int, trust: int, logical_id: str, payload: bytes) -> str:
    return require_rust().record_id_hex(kind, trust, logical_id, payload)


def rust_crc32(data: bytes) -> int:
    return require_rust().rust_crc32(data)
