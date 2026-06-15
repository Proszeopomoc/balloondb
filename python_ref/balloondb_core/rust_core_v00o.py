"""Rust/PyO3 bridge for BalloonDB.

V00O kept a BRS1 lab format. V00O3 adds drop-in compatibility with
python_ref.balloondb_core.binary_format_v00j, so Rust can read/write the
existing .bseed/.bbridge/.bwal file layout instead of introducing a second
main storage format.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Any

from . import binary_format_v00j as _pyv00j
from .binary_format_v00j import BinaryRecord

try:
    import balloondb_core_rs as _rs
except Exception as exc:  # pragma: no cover
    _rs = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


def rust_available() -> bool:
    return _rs is not None


def require_rust():
    if _rs is None:
        raise RuntimeError(f"balloondb_core_rs extension not available: {_IMPORT_ERROR}")
    return _rs


# Legacy/lab BRS1 functions from V00O. These are not the default storage format.
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


# V00J drop-in compatibility layer.
def _payload_bytes_from_records(records: Iterable[dict[str, Any]]) -> list[bytes]:
    return [_pyv00j.canonical_payload(row) for row in list(records)]


def v00j_record_id_u64(payload_bytes: bytes, *, prefer_rust: bool = True) -> int:
    if prefer_rust and rust_available():
        return int(require_rust().v00j_record_id_u64(payload_bytes))
    return _pyv00j.record_id_from_payload(payload_bytes)


def write_records_v00j(path: str | Path, kind: int, records: Iterable[dict[str, Any]], *, prefer_rust: bool = True) -> dict[str, Any]:
    path = Path(path)
    rows = list(records)
    if prefer_rust and rust_available():
        payloads = [_pyv00j.canonical_payload(row) for row in rows]
        data = bytes(require_rust().v00j_encode_file(int(kind), payloads))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return {
            "path": str(path),
            "kind": int(kind),
            "record_count": len(rows),
            "bytes": path.stat().st_size,
            "sha256": _pyv00j.sha256_file(path),
            "backend": "rust_v00j",
        }
    result = _pyv00j.write_records(path, kind, rows)
    result["backend"] = "python_v00j"
    return result


def read_records_v00j(path: str | Path, expected_kind: int | None = None, *, prefer_rust: bool = True) -> tuple[dict[str, Any], list[BinaryRecord]]:
    path = Path(path)
    if prefer_rust and rust_available():
        expected = 0 if expected_kind is None else int(expected_kind)
        decoded = require_rust().v00j_decode_file(path.read_bytes(), expected)
        header = dict(decoded["header"])
        out: list[BinaryRecord] = []
        for rec in decoded["records"]:
            payload_bytes = bytes(rec["payload"])
            payload = json.loads(payload_bytes.decode("utf-8"))
            out.append(BinaryRecord(
                record_id=int(rec["record_id"]),
                payload=payload,
                crc32=int(rec["crc32"]),
                flags=int(rec["flags"]),
            ))
        return header, out
    return _pyv00j.read_records(path, expected_kind=expected_kind)


def write_bseed_v00j(path: str | Path, records: Iterable[dict[str, Any]], *, prefer_rust: bool = True) -> dict[str, Any]:
    return write_records_v00j(path, _pyv00j.KIND_SEED, records, prefer_rust=prefer_rust)


def read_bseed_v00j(path: str | Path, *, prefer_rust: bool = True) -> tuple[dict[str, Any], list[BinaryRecord]]:
    return read_records_v00j(path, _pyv00j.KIND_SEED, prefer_rust=prefer_rust)


def write_bbridge_v00j(path: str | Path, records: Iterable[dict[str, Any]], *, prefer_rust: bool = True) -> dict[str, Any]:
    return write_records_v00j(path, _pyv00j.KIND_BRIDGE, records, prefer_rust=prefer_rust)


def read_bbridge_v00j(path: str | Path, *, prefer_rust: bool = True) -> tuple[dict[str, Any], list[BinaryRecord]]:
    return read_records_v00j(path, _pyv00j.KIND_BRIDGE, prefer_rust=prefer_rust)