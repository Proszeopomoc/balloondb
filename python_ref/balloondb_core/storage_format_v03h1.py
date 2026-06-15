
import json
import os
import struct
import time
import hashlib
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Union

MAGIC = b"BDH1"
VERSION = 1
HEADER = struct.Struct(">4sBBQI32s")
HEADER_SIZE = HEADER.size

RECORD_TYPES = {
    "SEED": 1,
    "BRIDGE": 2,
    "ROUTE": 3,
    "RESULT": 4,
    "META": 5,
}
RECORD_TYPE_NAMES = {v: k for k, v in RECORD_TYPES.items()}

class BalloonStorageError(Exception):
    pass

def now_ms() -> int:
    return int(time.time() * 1000)

def canonical_json_bytes(payload: Dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def checksum(record_type_id: int, timestamp_ms: int, payload_len: int, payload_bytes: bytes) -> bytes:
    h = hashlib.sha256()
    h.update(MAGIC)
    h.update(bytes([VERSION]))
    h.update(bytes([record_type_id]))
    h.update(struct.pack(">Q", timestamp_ms))
    h.update(struct.pack(">I", payload_len))
    h.update(payload_bytes)
    return h.digest()

def normalize_record_type(record_type: Union[str, int]) -> Tuple[int, str]:
    if isinstance(record_type, str):
        key = record_type.upper().strip()
        if key not in RECORD_TYPES:
            raise BalloonStorageError(f"unknown record type: {record_type}")
        return RECORD_TYPES[key], key
    if isinstance(record_type, int) and record_type in RECORD_TYPE_NAMES:
        return record_type, RECORD_TYPE_NAMES[record_type]
    raise BalloonStorageError(f"unknown record type id: {record_type}")

def validate_payload(record_type_name: str, payload: Dict) -> Dict:
    if not isinstance(payload, dict):
        raise BalloonStorageError("payload must be dict")
    p = dict(payload)
    p.setdefault("record_kind", record_type_name)
    p.setdefault("status", "OBSERVED")
    p.setdefault("schema_version", "V03H1")
    p.setdefault("created_ts", now_ms())

    if record_type_name == "SEED":
        for key in ("seed_id", "seed_type"):
            if not str(p.get(key, "")).strip():
                raise BalloonStorageError(f"SEED payload missing {key}")
    elif record_type_name == "BRIDGE":
        for key in ("bridge_id", "from_seed", "to_seed", "bridge_type"):
            if not str(p.get(key, "")).strip():
                raise BalloonStorageError(f"BRIDGE payload missing {key}")
    elif record_type_name == "ROUTE":
        p.setdefault("steps", [])
        if not str(p.get("route_id", "")).strip():
            raise BalloonStorageError("ROUTE payload missing route_id")
    elif record_type_name == "RESULT":
        if not str(p.get("result_id", "")).strip():
            raise BalloonStorageError("RESULT payload missing result_id")
    elif record_type_name == "META":
        if not str(p.get("meta_id", "")).strip():
            raise BalloonStorageError("META payload missing meta_id")

    canonical_json_bytes(p)
    return p

def append_record(path: Union[str, Path], record_type: Union[str, int], payload: Dict, fsync: bool = True) -> Dict:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    record_type_id, record_type_name = normalize_record_type(record_type)
    valid_payload = validate_payload(record_type_name, payload)
    payload_bytes = canonical_json_bytes(valid_payload)
    ts = now_ms()
    ck = checksum(record_type_id, ts, len(payload_bytes), payload_bytes)
    header = HEADER.pack(MAGIC, VERSION, record_type_id, ts, len(payload_bytes), ck)

    offset = target.stat().st_size if target.exists() else 0
    with target.open("ab") as f:
        f.write(header)
        f.write(payload_bytes)
        if fsync:
            f.flush()
            os.fsync(f.fileno())

    return {
        "status": "PASS_V03H1_RECORD_APPENDED",
        "path": str(target),
        "offset": offset,
        "record_type": record_type_name,
        "record_type_id": record_type_id,
        "timestamp_ms": ts,
        "payload_len": len(payload_bytes),
        "checksum_sha256": ck.hex().upper(),
    }

def iter_records(path: Union[str, Path], verify: bool = True, stop_on_partial: bool = True) -> Iterable[Dict]:
    target = Path(path)
    if not target.exists():
        return
    with target.open("rb") as f:
        offset = 0
        while True:
            raw_header = f.read(HEADER_SIZE)
            if raw_header == b"":
                break
            if len(raw_header) < HEADER_SIZE:
                if stop_on_partial:
                    break
                raise BalloonStorageError(f"partial header at offset {offset}")

            magic, version, record_type_id, ts, payload_len, ck = HEADER.unpack(raw_header)
            if magic != MAGIC:
                raise BalloonStorageError(f"bad magic at offset {offset}")
            if version != VERSION:
                raise BalloonStorageError(f"unsupported version {version} at offset {offset}")
            if record_type_id not in RECORD_TYPE_NAMES:
                raise BalloonStorageError(f"unknown record type id {record_type_id} at offset {offset}")
            payload_bytes = f.read(payload_len)
            if len(payload_bytes) < payload_len:
                if stop_on_partial:
                    break
                raise BalloonStorageError(f"partial payload at offset {offset}")
            expected = checksum(record_type_id, ts, payload_len, payload_bytes)
            checksum_ok = expected == ck
            if verify and not checksum_ok:
                raise BalloonStorageError(f"checksum mismatch at offset {offset}")
            try:
                payload = json.loads(payload_bytes.decode("utf-8"))
            except Exception as e:
                raise BalloonStorageError(f"json decode failed at offset {offset}: {e}") from e

            yield {
                "offset": offset,
                "record_type": RECORD_TYPE_NAMES[record_type_id],
                "record_type_id": record_type_id,
                "timestamp_ms": ts,
                "payload_len": payload_len,
                "checksum_sha256": ck.hex().upper(),
                "checksum_ok": checksum_ok,
                "payload": payload,
            }
            offset = f.tell()

def read_all_records(path: Union[str, Path], verify: bool = True) -> List[Dict]:
    return list(iter_records(path, verify=verify))

def build_index(records: List[Dict]) -> Dict:
    idx = {
        "total": 0,
        "by_type": {},
        "seed_ids": {},
        "bridge_ids": {},
        "route_ids": {},
        "result_ids": {},
        "last_offset": None,
    }
    for r in records:
        idx["total"] += 1
        t = r["record_type"]
        idx["by_type"][t] = idx["by_type"].get(t, 0) + 1
        p = r["payload"]
        if t == "SEED" and "seed_id" in p:
            idx["seed_ids"][p["seed_id"]] = r["offset"]
        if t == "BRIDGE" and "bridge_id" in p:
            idx["bridge_ids"][p["bridge_id"]] = r["offset"]
        if t == "ROUTE" and "route_id" in p:
            idx["route_ids"][p["route_id"]] = r["offset"]
        if t == "RESULT" and "result_id" in p:
            idx["result_ids"][p["result_id"]] = r["offset"]
        idx["last_offset"] = r["offset"]
    return idx

def create_seed(path: Union[str, Path], seed_id: str, seed_type: str, data: Dict, status: str = "OBSERVED") -> Dict:
    return append_record(path, "SEED", {
        "seed_id": seed_id,
        "seed_type": seed_type,
        "status": status,
        "data": data,
    })

def create_bridge(path: Union[str, Path], bridge_id: str, from_seed: str, to_seed: str, bridge_type: str, data: Optional[Dict] = None, status: str = "OBSERVED") -> Dict:
    return append_record(path, "BRIDGE", {
        "bridge_id": bridge_id,
        "from_seed": from_seed,
        "to_seed": to_seed,
        "bridge_type": bridge_type,
        "status": status,
        "data": data or {},
    })

def create_route(path: Union[str, Path], route_id: str, steps: List[Dict], status: str = "OBSERVED") -> Dict:
    return append_record(path, "ROUTE", {
        "route_id": route_id,
        "steps": steps,
        "status": status,
    })

def create_result(path: Union[str, Path], result_id: str, result_status: str, evidence: Dict) -> Dict:
    return append_record(path, "RESULT", {
        "result_id": result_id,
        "result_status": result_status,
        "evidence": evidence,
        "status": "OBSERVED",
    })
