from __future__ import annotations

import binascii
import hashlib
import json
import struct
from typing import Iterable, Mapping, Sequence, Any

RECORD_HEADER = "<QIIII"

def canonical_payload(row: Mapping[str, Any]) -> bytes:
    return json.dumps(
        row,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

def record_id_u64(payload: bytes) -> int:
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "little")

def encode_record_python(kind: int, trust: int, payload: bytes) -> bytes:
    payload = bytes(payload)
    return struct.pack(
        RECORD_HEADER,
        record_id_u64(payload),
        int(kind),
        int(trust),
        len(payload),
        binascii.crc32(payload) & 0xFFFFFFFF,
    ) + payload

def encode_batch_python(records: Sequence[tuple[int, int, bytes]]) -> list[bytes]:
    return [encode_record_python(k, t, p) for k, t, p in records]

def _rust_module():
    import balloondb_core_rs  # type: ignore
    return balloondb_core_rs

def rust_available() -> bool:
    try:
        m = _rust_module()
        return hasattr(m, "v00j_batch_encode_records")
    except Exception:
        return False

def encode_batch_rust(records: Sequence[tuple[int, int, bytes]]) -> list[bytes]:
    m = _rust_module()
    return list(m.v00j_batch_encode_records([(int(k), int(t), bytes(p)) for k, t, p in records]))

def count_payload_bytes_rust(records: Sequence[tuple[int, int, bytes]]) -> int:
    m = _rust_module()
    return int(m.v00j_batch_count_payload_bytes([(int(k), int(t), bytes(p)) for k, t, p in records]))

def encode_batch(records: Sequence[tuple[int, int, bytes]], backend: str = "auto") -> tuple[str, list[bytes]]:
    if backend == "python":
        return "python", encode_batch_python(records)
    if backend == "rust":
        return "rust", encode_batch_rust(records)
    if backend != "auto":
        raise ValueError(f"unknown backend: {backend}")
    if rust_available():
        return "rust", encode_batch_rust(records)
    return "python", encode_batch_python(records)
