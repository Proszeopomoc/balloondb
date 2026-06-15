"""Rust/PyO3 bridge for BalloonDB.

V00O kept BRS1 as a lab/legacy Rust format. V00O3A defines the real boundary:
Rust must operate byte-for-byte on the existing Python V00J wire format.
Rust does not serialize JSON. Python canonicalizes payload rows, then passes
canonical UTF-8 JSON bytes to Rust for V00J framing.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Iterable

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


# Legacy/lab BRS1 functions. Not the default DB format.
def encode_record(kind: int, trust: int, logical_id: str, payload: bytes) -> bytes:
    return bytes(require_rust().encode_record(kind, trust, logical_id, payload))


def decode_record(data: bytes) -> dict[str, Any]:
    d = dict(require_rust().decode_record(data))
    d["payload"] = bytes(d["payload"])
    return d


def record_id_hex(kind: int, trust: int, logical_id: str, payload: bytes) -> str:
    return str(require_rust().record_id_hex(kind, trust, logical_id, payload))


def rust_crc32(data: bytes) -> int:
    return int(require_rust().rust_crc32(data))


# V00J strict drop-in compatibility.
def canonical_payload(row: dict[str, Any]) -> bytes:
    return _pyv00j.canonical_payload(row)


def canonical_payloads(records: Iterable[dict[str, Any]]) -> list[bytes]:
    return [canonical_payload(row) for row in list(records)]


def v00j_record_id(payload_bytes: bytes, *, prefer_rust: bool = True) -> int:
    if prefer_rust and rust_available():
        return int(require_rust().v00j_record_id(payload_bytes))
    return int(_pyv00j.record_id_from_payload(payload_bytes))


def v00j_write_file_bytes(kind: int, created_ms: int, payload_bytes_list: Iterable[bytes], *, prefer_rust: bool = True) -> bytes:
    payloads = [bytes(p) for p in payload_bytes_list]
    if prefer_rust and rust_available():
        return bytes(require_rust().v00j_write_file(int(kind), int(created_ms), payloads))
    # Reference Python writer with deterministic created_ms, independent of private module internals.
    import struct, zlib, hashlib
    magic = {1: b"BSEEDJ00", 2: b"BBRDGJ00", 3: b"BWAL0J00"}[int(kind)]
    out = struct.pack("<8sHHIQQ32s", magic, 1, int(kind), 64, int(created_ms), len(payloads), b"\x00" * 32)
    for payload in payloads:
        rid = int.from_bytes(hashlib.sha256(payload).digest()[:8], "little")
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        out += struct.pack("<QIIII", rid, len(payload), crc, 0, 0) + payload
    return out


def write_records_v00j(
    path: str | Path,
    kind: int,
    records: Iterable[dict[str, Any]],
    *,
    prefer_rust: bool = True,
    created_ms: int | None = None,
) -> dict[str, Any]:
    path = Path(path)
    rows = list(records)
    if prefer_rust and rust_available():
        if created_ms is None:
            created_ms = int(time.time() * 1000)
        data = v00j_write_file_bytes(int(kind), int(created_ms), canonical_payloads(rows), prefer_rust=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return {
            "path": str(path),
            "kind": int(kind),
            "record_count": len(rows),
            "bytes": path.stat().st_size,
            "sha256": _pyv00j.sha256_file(path),
            "backend": "rust_v00j",
            "created_ms": int(created_ms),
        }
    result = _pyv00j.write_records(path, kind, rows)
    result["backend"] = "python_v00j"
    return result


def read_records_v00j(path: str | Path, expected_kind: int | None = None, *, prefer_rust: bool = True) -> tuple[dict[str, Any], list[BinaryRecord]]:
    path = Path(path)
    if prefer_rust and rust_available():
        decoded = require_rust().v00j_read_file(path.read_bytes())
        header = dict(decoded["header"])
        if expected_kind is not None and int(header["kind"]) != int(expected_kind):
            raise ValueError(f"kind mismatch: expected {expected_kind}, got {header['kind']}")
        out: list[BinaryRecord] = []
        for rec in decoded["records"]:
            payload_bytes = bytes(rec["payload"])
            payload = json.loads(payload_bytes.decode("utf-8"))
            out.append(BinaryRecord(record_id=int(rec["record_id"]), payload=payload, crc32=int(rec["crc32"]), flags=int(rec["flags"])))
        return header, out
    return _pyv00j.read_records(path, expected_kind=expected_kind)


def write_bseed_v00j(path: str | Path, records: Iterable[dict[str, Any]], *, prefer_rust: bool = True, created_ms: int | None = None) -> dict[str, Any]:
    return write_records_v00j(path, _pyv00j.KIND_SEED, records, prefer_rust=prefer_rust, created_ms=created_ms)


def read_bseed_v00j(path: str | Path, *, prefer_rust: bool = True) -> tuple[dict[str, Any], list[BinaryRecord]]:
    return read_records_v00j(path, _pyv00j.KIND_SEED, prefer_rust=prefer_rust)


def write_bbridge_v00j(path: str | Path, records: Iterable[dict[str, Any]], *, prefer_rust: bool = True, created_ms: int | None = None) -> dict[str, Any]:
    return write_records_v00j(path, _pyv00j.KIND_BRIDGE, records, prefer_rust=prefer_rust, created_ms=created_ms)


def read_bbridge_v00j(path: str | Path, *, prefer_rust: bool = True) -> tuple[dict[str, Any], list[BinaryRecord]]:
    return read_records_v00j(path, _pyv00j.KIND_BRIDGE, prefer_rust=prefer_rust)
