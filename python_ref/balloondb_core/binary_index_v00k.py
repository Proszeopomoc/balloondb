from __future__ import annotations

import json
import re
import struct
import time
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from balloondb_core.binary_format_v00j import (
    BinaryRecord,
    BalloonBinaryChecksumError,
    BalloonBinaryFormatError,
    read_bbridge,
    read_bseed,
    sha256_file,
)

VERSION = 1
INDEX_MAGIC = b"BINDXK00"
HEADER_SIZE = 40
INDEX_HEADER = struct.Struct("<8sHHIQI12s")


class BalloonBinaryIndexError(Exception):
    pass


class BalloonBinaryIndexChecksumError(BalloonBinaryIndexError):
    pass


class BalloonBinaryIndexFormatError(BalloonBinaryIndexError):
    pass


@dataclass(frozen=True)
class IndexEntry:
    record_id: int
    source_file: str
    source_kind: str
    record_index: int
    payload_type: str
    trust_state: str
    logical_id: str
    relation: str


def now_ms() -> int:
    return int(time.time() * 1000)


def canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _payload_type(source_kind: str, payload: dict[str, Any]) -> str:
    if "type" in payload and payload["type"]:
        return str(payload["type"])
    if source_kind == "bbridge" and payload.get("relation"):
        return str(payload["relation"])
    if payload.get("kind"):
        return str(payload["kind"])
    return source_kind.upper()


def _logical_id(source_kind: str, payload: dict[str, Any], record_id: int) -> str:
    for key in ("seed_id", "bridge_id", "id", "key"):
        if payload.get(key):
            return str(payload[key])
    return f"rid:{record_id}"


def _entry_from_record(source_path: Path, source_kind: str, index: int, record: BinaryRecord) -> IndexEntry:
    payload = record.payload
    return IndexEntry(
        record_id=int(record.record_id),
        source_file=str(source_path),
        source_kind=source_kind,
        record_index=int(index),
        payload_type=_payload_type(source_kind, payload),
        trust_state=str(payload.get("trust_state", "RAW")),
        logical_id=_logical_id(source_kind, payload, int(record.record_id)),
        relation=str(payload.get("relation", "")),
    )


def _add_lookup(mapping: dict[str, list[int]], key: str, pos: int) -> None:
    if key not in mapping:
        mapping[key] = []
    mapping[key].append(pos)


def build_index_payload(entries: Iterable[IndexEntry]) -> dict[str, Any]:
    rows = [e.__dict__ for e in entries]
    rows.sort(key=lambda r: (r["source_kind"], r["record_index"], r["record_id"]))
    by_record_id: dict[str, list[int]] = {}
    by_type: dict[str, list[int]] = {}
    by_trust_state: dict[str, list[int]] = {}
    by_relation: dict[str, list[int]] = {}
    by_logical_id: dict[str, list[int]] = {}

    for pos, row in enumerate(rows):
        _add_lookup(by_record_id, str(row["record_id"]), pos)
        _add_lookup(by_type, row["payload_type"], pos)
        _add_lookup(by_trust_state, row["trust_state"], pos)
        _add_lookup(by_logical_id, row["logical_id"], pos)
        if row.get("relation"):
            _add_lookup(by_relation, row["relation"], pos)

    return {
        "format": "BALLOONDB_BINARY_INDEX_V00K",
        "version": VERSION,
        "created_ms": now_ms(),
        "record_count": len(rows),
        "records": rows,
        "lookups": {
            "record_id": by_record_id,
            "type": by_type,
            "trust_state": by_trust_state,
            "relation": by_relation,
            "logical_id": by_logical_id,
        },
    }


def write_index(path: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload_bytes = canonical_payload(payload)
    crc = zlib.crc32(payload_bytes) & 0xFFFFFFFF
    header = INDEX_HEADER.pack(INDEX_MAGIC, VERSION, HEADER_SIZE, len(payload_bytes), now_ms(), crc, b"\x00" * 12)
    with path.open("wb") as f:
        f.write(header)
        f.write(payload_bytes)
    return {
        "path": str(path),
        "format": "BINDXK00",
        "version": VERSION,
        "record_count": int(payload.get("record_count", 0)),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "crc32": crc,
    }


def read_index(path: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    path = Path(path)
    with path.open("rb") as f:
        raw = f.read(HEADER_SIZE)
        if len(raw) != HEADER_SIZE:
            raise BalloonBinaryIndexFormatError("invalid index header length")
        magic, version, header_size, payload_len, created_ms, expected_crc, reserved = INDEX_HEADER.unpack(raw)
        if magic != INDEX_MAGIC:
            raise BalloonBinaryIndexFormatError(f"invalid index magic: {magic!r}")
        if version != VERSION:
            raise BalloonBinaryIndexFormatError(f"unsupported index version: {version}")
        if header_size != HEADER_SIZE:
            raise BalloonBinaryIndexFormatError(f"invalid index header_size: {header_size}")
        payload_bytes = f.read(payload_len)
        if len(payload_bytes) != payload_len:
            raise BalloonBinaryIndexFormatError("truncated index payload")
        actual_crc = zlib.crc32(payload_bytes) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise BalloonBinaryIndexChecksumError(f"index CRC mismatch: {actual_crc} != {expected_crc}")
        if f.read(1):
            raise BalloonBinaryIndexFormatError("unexpected trailing bytes in index")
        payload = json.loads(payload_bytes.decode("utf-8"))
        header = {
            "magic": magic.decode("ascii", errors="replace"),
            "version": version,
            "header_size": header_size,
            "payload_len": payload_len,
            "created_ms": created_ms,
            "crc32": expected_crc,
        }
        return header, payload


def build_index_from_files(index_path: str | Path, bseed_path: str | Path, bbridge_path: str | Path) -> dict[str, Any]:
    bseed_path = Path(bseed_path)
    bbridge_path = Path(bbridge_path)
    entries: list[IndexEntry] = []

    _seed_header, seed_records = read_bseed(bseed_path)
    for i, record in enumerate(seed_records):
        entries.append(_entry_from_record(bseed_path, "bseed", i, record))

    _bridge_header, bridge_records = read_bbridge(bbridge_path)
    for i, record in enumerate(bridge_records):
        entries.append(_entry_from_record(bbridge_path, "bbridge", i, record))

    payload = build_index_payload(entries)
    return write_index(index_path, payload)


def _lookup(index_payload: dict[str, Any], lookup_name: str, key: str) -> list[dict[str, Any]]:
    records = index_payload.get("records", [])
    positions = index_payload.get("lookups", {}).get(lookup_name, {}).get(str(key), [])
    return [records[int(pos)] for pos in positions]


def lookup_record_id(index_payload: dict[str, Any], record_id: int | str) -> list[dict[str, Any]]:
    return _lookup(index_payload, "record_id", str(record_id))


def lookup_type(index_payload: dict[str, Any], value: str) -> list[dict[str, Any]]:
    return _lookup(index_payload, "type", value)


def lookup_trust_state(index_payload: dict[str, Any], value: str) -> list[dict[str, Any]]:
    return _lookup(index_payload, "trust_state", value)


def lookup_relation(index_payload: dict[str, Any], value: str) -> list[dict[str, Any]]:
    return _lookup(index_payload, "relation", value)


def lookup_logical_id(index_payload: dict[str, Any], value: str) -> list[dict[str, Any]]:
    return _lookup(index_payload, "logical_id", value)


MINI_QUERY_RE = re.compile(r"^FIND\s+(record_id|type|trust_state|relation|logical_id)\s*=\s*(.+?)\s*$", re.IGNORECASE)


def binary_mini_query(index_payload: dict[str, Any], query: str) -> dict[str, Any]:
    m = MINI_QUERY_RE.match(query.strip())
    if not m:
        return {"ok": False, "status": "BINARY_QUERY_UNSUPPORTED_SYNTAX", "results": []}
    field = m.group(1).lower()
    value = m.group(2).strip().strip('"').strip("'")
    if field == "record_id":
        results = lookup_record_id(index_payload, value)
    elif field == "type":
        results = lookup_type(index_payload, value)
    elif field == "trust_state":
        results = lookup_trust_state(index_payload, value)
    elif field == "relation":
        results = lookup_relation(index_payload, value)
    elif field == "logical_id":
        results = lookup_logical_id(index_payload, value)
    else:
        return {"ok": False, "status": "BINARY_QUERY_UNSUPPORTED_FIELD", "results": []}
    return {"ok": True, "status": "PASS_BINARY_INDEX_QUERY", "field": field, "value": value, "count": len(results), "results": results}


def verify_index(path: str | Path) -> dict[str, Any]:
    header, payload = read_index(path)
    expected = int(payload.get("record_count", -1))
    actual = len(payload.get("records", []))
    if expected != actual:
        raise BalloonBinaryIndexFormatError(f"index record_count mismatch: {expected} != {actual}")
    return {
        "status": "PASS_BINARY_INDEX_VERIFY",
        "path": str(path),
        "record_count": actual,
        "sha256": sha256_file(Path(path)),
        "header": header,
    }


def corrupt_index_copy(src: str | Path, dst: str | Path) -> Path:
    src = Path(src)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    data = bytearray(src.read_bytes())
    if len(data) <= HEADER_SIZE + 2:
        raise BalloonBinaryIndexFormatError("index too small to corrupt")
    data[HEADER_SIZE + 1] ^= 0x55
    dst.write_bytes(bytes(data))
    return dst
