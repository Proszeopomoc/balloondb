
import json
import os
import struct
import time
import hashlib
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Union

MAGIC = b"BWAL"
VERSION = 1
HEADER = struct.Struct(">4sBBQI I 32s".replace(" ", ""))
HEADER_SIZE = HEADER.size

OP_TYPES = {
    "INTENT": 1,
    "COMMIT": 2,
    "ABORT": 3,
    "CHECKPOINT": 4,
}
OP_TYPE_NAMES = {v: k for k, v in OP_TYPES.items()}

class BalloonWALError(Exception):
    pass

def now_ms() -> int:
    return int(time.time() * 1000)

def canonical_json_bytes(payload: Dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def normalize_op_type(op_type: Union[str, int]) -> Tuple[int, str]:
    if isinstance(op_type, str):
        key = op_type.upper().strip()
        if key not in OP_TYPES:
            raise BalloonWALError(f"unknown WAL op type: {op_type}")
        return OP_TYPES[key], key
    if isinstance(op_type, int) and op_type in OP_TYPE_NAMES:
        return op_type, OP_TYPE_NAMES[op_type]
    raise BalloonWALError(f"unknown WAL op type id: {op_type}")

def checksum(op_type_id: int, timestamp_ms: int, seq: int, payload_len: int, payload_bytes: bytes) -> bytes:
    h = hashlib.sha256()
    h.update(MAGIC)
    h.update(bytes([VERSION]))
    h.update(bytes([op_type_id]))
    h.update(struct.pack(">Q", timestamp_ms))
    h.update(struct.pack(">I", seq))
    h.update(struct.pack(">I", payload_len))
    h.update(payload_bytes)
    return h.digest()

def next_seq(path: Union[str, Path]) -> int:
    max_seq = 0
    try:
        for rec in iter_wal_records(path, verify=True, stop_on_partial=True):
            max_seq = max(max_seq, int(rec["seq"]))
    except Exception:
        pass
    return max_seq + 1

def validate_payload(op_type_name: str, payload: Dict) -> Dict:
    if not isinstance(payload, dict):
        raise BalloonWALError("payload must be dict")
    p = dict(payload)
    p.setdefault("op_type", op_type_name)
    p.setdefault("schema_version", "V03H2")
    p.setdefault("created_ts", now_ms())

    if op_type_name in ("INTENT", "COMMIT", "ABORT"):
        if not str(p.get("tx_id", "")).strip():
            raise BalloonWALError(f"{op_type_name} payload missing tx_id")
    if op_type_name == "INTENT":
        if not str(p.get("action", "")).strip():
            raise BalloonWALError("INTENT payload missing action")
    canonical_json_bytes(p)
    return p

def append_wal_record(path: Union[str, Path], op_type: Union[str, int], payload: Dict, fsync: bool = True) -> Dict:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    op_type_id, op_type_name = normalize_op_type(op_type)
    valid_payload = validate_payload(op_type_name, payload)
    payload_bytes = canonical_json_bytes(valid_payload)
    ts = now_ms()
    seq = next_seq(target)
    ck = checksum(op_type_id, ts, seq, len(payload_bytes), payload_bytes)
    header = HEADER.pack(MAGIC, VERSION, op_type_id, ts, seq, len(payload_bytes), ck)
    offset = target.stat().st_size if target.exists() else 0

    with target.open("ab") as f:
        f.write(header)
        f.write(payload_bytes)
        if fsync:
            f.flush()
            os.fsync(f.fileno())

    return {
        "status": "PASS_V03H2_WAL_RECORD_APPENDED",
        "path": str(target),
        "offset": offset,
        "op_type": op_type_name,
        "op_type_id": op_type_id,
        "seq": seq,
        "timestamp_ms": ts,
        "payload_len": len(payload_bytes),
        "checksum_sha256": ck.hex().upper(),
    }

def iter_wal_records(path: Union[str, Path], verify: bool = True, stop_on_partial: bool = True) -> Iterable[Dict]:
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
                raise BalloonWALError(f"partial WAL header at offset {offset}")

            magic, version, op_type_id, ts, seq, payload_len, ck = HEADER.unpack(raw_header)
            if magic != MAGIC:
                raise BalloonWALError(f"bad WAL magic at offset {offset}")
            if version != VERSION:
                raise BalloonWALError(f"unsupported WAL version {version} at offset {offset}")
            if op_type_id not in OP_TYPE_NAMES:
                raise BalloonWALError(f"unknown WAL op type {op_type_id} at offset {offset}")

            payload_bytes = f.read(payload_len)
            if len(payload_bytes) < payload_len:
                if stop_on_partial:
                    break
                raise BalloonWALError(f"partial WAL payload at offset {offset}")

            expected = checksum(op_type_id, ts, seq, payload_len, payload_bytes)
            checksum_ok = expected == ck
            if verify and not checksum_ok:
                raise BalloonWALError(f"WAL checksum mismatch at offset {offset}")

            try:
                payload = json.loads(payload_bytes.decode("utf-8"))
            except Exception as e:
                raise BalloonWALError(f"WAL JSON decode failed at offset {offset}: {e}") from e

            yield {
                "offset": offset,
                "op_type": OP_TYPE_NAMES[op_type_id],
                "op_type_id": op_type_id,
                "seq": seq,
                "timestamp_ms": ts,
                "payload_len": payload_len,
                "checksum_sha256": ck.hex().upper(),
                "checksum_ok": checksum_ok,
                "payload": payload,
            }
            offset = f.tell()

def read_wal_records(path: Union[str, Path], verify: bool = True) -> List[Dict]:
    return list(iter_wal_records(path, verify=verify, stop_on_partial=True))

def begin_transaction(path: Union[str, Path], tx_id: str, action: str, data: Dict, target_path: Optional[str] = None) -> Dict:
    payload = {
        "tx_id": tx_id,
        "action": action,
        "data": data,
    }
    if target_path:
        payload["target_path"] = str(target_path)
    return append_wal_record(path, "INTENT", payload)

def commit_transaction(path: Union[str, Path], tx_id: str) -> Dict:
    return append_wal_record(path, "COMMIT", {"tx_id": tx_id})

def abort_transaction(path: Union[str, Path], tx_id: str, reason: str = "") -> Dict:
    return append_wal_record(path, "ABORT", {"tx_id": tx_id, "reason": reason})

def recover_transactions(path: Union[str, Path]) -> Dict:
    intents: Dict[str, Dict] = {}
    commits = set()
    aborts = set()
    records = read_wal_records(path, verify=True)

    for rec in records:
        payload = rec["payload"]
        tx_id = payload.get("tx_id")
        if rec["op_type"] == "INTENT":
            intents[tx_id] = rec
        elif rec["op_type"] == "COMMIT":
            commits.add(tx_id)
        elif rec["op_type"] == "ABORT":
            aborts.add(tx_id)

    committed = []
    pending = []
    aborted = []
    for tx_id, intent in intents.items():
        if tx_id in aborts:
            aborted.append(intent)
        elif tx_id in commits:
            committed.append(intent)
        else:
            pending.append(intent)

    committed.sort(key=lambda r: r["seq"])
    pending.sort(key=lambda r: r["seq"])
    aborted.sort(key=lambda r: r["seq"])

    return {
        "status": "PASS_V03H2_WAL_RECOVERY_SCAN",
        "record_count": len(records),
        "committed_count": len(committed),
        "pending_count": len(pending),
        "aborted_count": len(aborted),
        "committed": committed,
        "pending": pending,
        "aborted": aborted,
    }

def apply_committed_append_records(wal_path: Union[str, Path], store_path: Union[str, Path], applied_tx_ids: Optional[set] = None) -> Dict:
    from balloondb_core.storage_format_v03h1 import append_record

    applied_tx_ids = applied_tx_ids or set()
    recovery = recover_transactions(wal_path)
    applied = []
    skipped = []

    for intent in recovery["committed"]:
        payload = intent["payload"]
        tx_id = payload.get("tx_id")
        if tx_id in applied_tx_ids:
            skipped.append({"tx_id": tx_id, "reason": "already_applied"})
            continue
        if payload.get("action") != "append_record":
            skipped.append({"tx_id": tx_id, "reason": "unsupported_action", "action": payload.get("action")})
            continue

        data = payload.get("data") or {}
        record_type = data.get("record_type")
        record_payload = data.get("payload")
        res = append_record(store_path, record_type, record_payload)
        applied_tx_ids.add(tx_id)
        applied.append({"tx_id": tx_id, "append_result": res})

    return {
        "status": "PASS_V03H2_WAL_COMMITTED_RECORDS_APPLIED",
        "wal_path": str(wal_path),
        "store_path": str(store_path),
        "applied_count": len(applied),
        "skipped_count": len(skipped),
        "applied": applied,
        "skipped": skipped,
        "recovery_summary": {
            "record_count": recovery["record_count"],
            "committed_count": recovery["committed_count"],
            "pending_count": recovery["pending_count"],
            "aborted_count": recovery["aborted_count"],
        },
    }
