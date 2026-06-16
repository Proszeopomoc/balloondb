#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V00P Rust backend shim for the existing V00J byte contract."""
from __future__ import annotations

import binascii
import hashlib
import json
import os
import struct
from typing import Any, Dict, Tuple

RECORD_HEADER_STRUCT = struct.Struct("<QIIII")


def canonical_payload(row: Dict[str, Any]) -> bytes:
    return json.dumps(
        row,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def python_v00j_record_id_u64(payload: bytes) -> int:
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "little")


def python_v00j_crc32(payload: bytes) -> int:
    return binascii.crc32(payload) & 0xFFFFFFFF


def python_encode_record_from_payload(payload: bytes, kind: int = 1, trust: int = 1) -> bytes:
    # kind/trust are accepted for shim symmetry but V00J record header itself has no kind/trust fields.
    rid = python_v00j_record_id_u64(payload)
    crc = python_v00j_crc32(payload)
    return RECORD_HEADER_STRUCT.pack(rid, len(payload), crc, 0, 0) + payload


def _import_rust():
    if os.environ.get("BALLOONDB_DISABLE_RUST") == "1":
        return None
    try:
        import balloondb_core_rs  # type: ignore
        return balloondb_core_rs
    except Exception:
        return None


def rust_available() -> bool:
    rs = _import_rust()
    return bool(rs is not None and hasattr(rs, "v00j_record_id") and hasattr(rs, "v00j_encode_record"))


def selected_backend() -> str:
    return "rust" if rust_available() else "python"


def _normalize_rust_record_id(value: Any) -> int:
    if isinstance(value, int):
        return value & 0xFFFFFFFFFFFFFFFF
    if isinstance(value, bytes):
        if len(value) >= 8:
            return int.from_bytes(value[:8], "little")
        return int(value.hex(), 16)
    if isinstance(value, str):
        s = value.strip().lower()
        if s.startswith("0x"):
            return int(s, 16) & 0xFFFFFFFFFFFFFFFF
        if len(s) >= 16 and all(c in "0123456789abcdef" for c in s[:16]):
            raw = bytes.fromhex(s[:16])
            return int.from_bytes(raw, "little") & 0xFFFFFFFFFFFFFFFF
        return int(s) & 0xFFFFFFFFFFFFFFFF
    return int(value) & 0xFFFFFFFFFFFFFFFF


def rust_v00j_record_id_u64(payload: bytes) -> int:
    rs = _import_rust()
    if rs is None or not hasattr(rs, "v00j_record_id"):
        raise RuntimeError("RUST_V00J_RECORD_ID_UNAVAILABLE")
    return _normalize_rust_record_id(rs.v00j_record_id(payload))


def rust_v00j_crc32(payload: bytes) -> int:
    rs = _import_rust()
    if rs is None:
        raise RuntimeError("RUST_BACKEND_UNAVAILABLE")
    if hasattr(rs, "v00j_crc32"):
        return int(rs.v00j_crc32(payload)) & 0xFFFFFFFF
    if hasattr(rs, "rust_crc32"):
        return int(rs.rust_crc32(payload)) & 0xFFFFFFFF
    raise RuntimeError("RUST_CRC32_UNAVAILABLE")


def _try_rust_encode_record(payload: bytes, kind: int, trust: int) -> bytes:
    rs = _import_rust()
    if rs is None or not hasattr(rs, "v00j_encode_record"):
        raise RuntimeError("RUST_V00J_ENCODE_RECORD_UNAVAILABLE")
    f = rs.v00j_encode_record
    attempts: Tuple[Tuple[Any, ...], ...] = (
        (payload, int(kind), int(trust)),
        (int(kind), int(trust), payload),
        (int(kind), payload, int(trust)),
        (payload,),
    )
    errors = []
    for args in attempts:
        try:
            out = f(*args)
            if isinstance(out, bytes):
                return out
            if isinstance(out, bytearray):
                return bytes(out)
            if isinstance(out, memoryview):
                return out.tobytes()
        except TypeError as exc:
            errors.append(str(exc))
    raise RuntimeError("RUST_V00J_ENCODE_RECORD_SIGNATURE_UNSUPPORTED: " + " | ".join(errors[:3]))


def encode_record_from_payload(payload: bytes, kind: int = 1, trust: int = 1, backend: str = "auto") -> bytes:
    if backend == "python":
        return python_encode_record_from_payload(payload, kind=kind, trust=trust)
    if backend == "rust":
        return _try_rust_encode_record(payload, kind=kind, trust=trust)
    if backend != "auto":
        raise ValueError(f"unknown backend: {backend}")
    if rust_available():
        return _try_rust_encode_record(payload, kind=kind, trust=trust)
    return python_encode_record_from_payload(payload, kind=kind, trust=trust)


def encode_record(row: Dict[str, Any], kind: int = 1, trust: int = 1, backend: str = "auto") -> bytes:
    return encode_record_from_payload(canonical_payload(row), kind=kind, trust=trust, backend=backend)


def record_id_u64(row: Dict[str, Any], backend: str = "auto") -> int:
    payload = canonical_payload(row)
    if backend == "python":
        return python_v00j_record_id_u64(payload)
    if backend == "rust":
        return rust_v00j_record_id_u64(payload)
    if backend != "auto":
        raise ValueError(f"unknown backend: {backend}")
    return rust_v00j_record_id_u64(payload) if rust_available() else python_v00j_record_id_u64(payload)
