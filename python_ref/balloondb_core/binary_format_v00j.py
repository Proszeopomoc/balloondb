from __future__ import annotations

import hashlib
import json
import os
import struct
import time
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

VERSION = 1
HEADER_SIZE = 64
RECORD_HEADER_SIZE = 24

KIND_SEED = 1
KIND_BRIDGE = 2
KIND_WAL = 3

MAGIC_BY_KIND = {
    KIND_SEED: b"BSEEDJ00",
    KIND_BRIDGE: b"BBRDGJ00",
    KIND_WAL: b"BWAL0J00",
}

KIND_BY_MAGIC = {v: k for k, v in MAGIC_BY_KIND.items()}

FILE_HEADER = struct.Struct("<8sHHIQQ32s")
RECORD_HEADER = struct.Struct("<QIIII")


class BalloonBinaryError(Exception):
    pass


class BalloonBinaryChecksumError(BalloonBinaryError):
    pass


class BalloonBinaryFormatError(BalloonBinaryError):
    pass


@dataclass(frozen=True)
class BinaryRecord:
    record_id: int
    payload: dict[str, Any]
    crc32: int
    flags: int = 0


def now_ms() -> int:
    return int(time.time() * 1000)


def canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def record_id_from_payload(payload_bytes: bytes) -> int:
    digest = hashlib.sha256(payload_bytes).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _pack_header(kind: int, record_count: int, created_ms: int | None = None) -> bytes:
    if kind not in MAGIC_BY_KIND:
        raise BalloonBinaryFormatError(f"unknown kind: {kind}")
    created = now_ms() if created_ms is None else int(created_ms)
    return FILE_HEADER.pack(
        MAGIC_BY_KIND[kind],
        VERSION,
        kind,
        HEADER_SIZE,
        created,
        int(record_count),
        b"\x00" * 32,
    )


def _unpack_header(raw: bytes) -> dict[str, Any]:
    if len(raw) != HEADER_SIZE:
        raise BalloonBinaryFormatError("invalid header length")
    magic, version, kind, header_size, created_ms, record_count, reserved = FILE_HEADER.unpack(raw)
    if magic not in KIND_BY_MAGIC:
        raise BalloonBinaryFormatError(f"invalid magic: {magic!r}")
    if version != VERSION:
        raise BalloonBinaryFormatError(f"unsupported version: {version}")
    if kind != KIND_BY_MAGIC[magic]:
        raise BalloonBinaryFormatError("kind/magic mismatch")
    if header_size != HEADER_SIZE:
        raise BalloonBinaryFormatError(f"invalid header_size: {header_size}")
    return {
        "magic": magic.decode("ascii", errors="replace"),
        "version": version,
        "kind": kind,
        "header_size": header_size,
        "created_ms": created_ms,
        "record_count": record_count,
    }


def write_records(path: str | Path, kind: int, records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    path = Path(path)
    rows = list(records)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        f.write(_pack_header(kind, len(rows)))
        for payload in rows:
            pb = canonical_payload(payload)
            rid = record_id_from_payload(pb)
            crc = zlib.crc32(pb) & 0xFFFFFFFF
            f.write(RECORD_HEADER.pack(rid, len(pb), crc, 0, 0))
            f.write(pb)
    return {
        "path": str(path),
        "kind": kind,
        "record_count": len(rows),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def read_records(path: str | Path, expected_kind: int | None = None) -> tuple[dict[str, Any], list[BinaryRecord]]:
    path = Path(path)
    with path.open("rb") as f:
        header = _unpack_header(f.read(HEADER_SIZE))
        if expected_kind is not None and header["kind"] != expected_kind:
            raise BalloonBinaryFormatError(f"unexpected kind: {header['kind']} != {expected_kind}")
        records: list[BinaryRecord] = []
        for index in range(header["record_count"]):
            rh = f.read(RECORD_HEADER_SIZE)
            if len(rh) != RECORD_HEADER_SIZE:
                raise BalloonBinaryFormatError(f"truncated record header at index {index}")
            record_id, payload_len, crc32_expected, flags, reserved = RECORD_HEADER.unpack(rh)
            payload_bytes = f.read(payload_len)
            if len(payload_bytes) != payload_len:
                raise BalloonBinaryFormatError(f"truncated payload at index {index}")
            crc32_actual = zlib.crc32(payload_bytes) & 0xFFFFFFFF
            if crc32_actual != crc32_expected:
                raise BalloonBinaryChecksumError(
                    f"CRC mismatch at index {index}: {crc32_actual} != {crc32_expected}"
                )
            payload = json.loads(payload_bytes.decode("utf-8"))
            calculated_id = record_id_from_payload(payload_bytes)
            if calculated_id != record_id:
                raise BalloonBinaryChecksumError(
                    f"record id mismatch at index {index}: {calculated_id} != {record_id}"
                )
            records.append(BinaryRecord(record_id=record_id, payload=payload, crc32=crc32_actual, flags=flags))
        trailing = f.read(1)
        if trailing:
            raise BalloonBinaryFormatError("unexpected trailing bytes")
        return header, records


def verify_records(path: str | Path, expected_kind: int | None = None) -> dict[str, Any]:
    header, records = read_records(path, expected_kind=expected_kind)
    return {
        "status": "PASS_BINARY_VERIFY",
        "path": str(path),
        "kind": header["kind"],
        "record_count": len(records),
        "sha256": sha256_file(Path(path)),
    }


def write_bseed(path: str | Path, records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    return write_records(path, KIND_SEED, records)


def read_bseed(path: str | Path) -> tuple[dict[str, Any], list[BinaryRecord]]:
    return read_records(path, expected_kind=KIND_SEED)


def write_bbridge(path: str | Path, records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    return write_records(path, KIND_BRIDGE, records)


def read_bbridge(path: str | Path) -> tuple[dict[str, Any], list[BinaryRecord]]:
    return read_records(path, expected_kind=KIND_BRIDGE)


def write_bwal(path: str | Path, wal_entries: Iterable[dict[str, Any]]) -> dict[str, Any]:
    return write_records(path, KIND_WAL, wal_entries)


def replay_bwal(path: str | Path) -> list[dict[str, Any]]:
    _header, records = read_records(path, expected_kind=KIND_WAL)
    return [r.payload for r in records]


def corrupt_copy(src: str | Path, dst: str | Path, offset: int | None = None) -> Path:
    src = Path(src)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    data = bytearray(src.read_bytes())
    if len(data) <= HEADER_SIZE + RECORD_HEADER_SIZE + 2:
        raise BalloonBinaryFormatError("file too small to corrupt")
    pos = offset if offset is not None else HEADER_SIZE + RECORD_HEADER_SIZE + 1
    data[pos] ^= 0x7F
    dst.write_bytes(bytes(data))
    return dst


def write_manifest(path: str | Path, files: list[dict[str, Any]], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    path = Path(path)
    payload = {
        "format": "BALLOONDB_MANIFEST_V00J",
        "version": VERSION,
        "created_ms": now_ms(),
        "files": files,
        "extra": extra or {},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    payload["path"] = str(path)
    payload["sha256"] = sha256_file(path)
    return payload
