
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from balloondb_core.storage_format_v03h1 import append_record, read_all_records, build_index
from balloondb_core.wal_v03h2 import recover_transactions

class BalloonCrashRecoveryError(Exception):
    pass

def now_ms() -> int:
    return int(time.time() * 1000)

def default_state_path(store_path: Union[str, Path]) -> Path:
    store = Path(store_path)
    return store.with_suffix(store.suffix + ".recovery_state.json")

def load_recovery_state(state_path: Union[str, Path]) -> Dict:
    p = Path(state_path)
    if not p.exists():
        return {
            "schema_version": "V03H3",
            "applied_tx_ids": [],
            "created_ts": now_ms(),
            "updated_ts": now_ms(),
        }
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig", errors="replace"))
    except Exception as e:
        raise BalloonCrashRecoveryError(f"failed to read recovery state: {p}: {e}") from e
    data.setdefault("schema_version", "V03H3")
    data.setdefault("applied_tx_ids", [])
    data.setdefault("updated_ts", now_ms())
    return data

def atomic_write_json(path: Union[str, Path], obj: Dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)

def recover_database(
    wal_path: Union[str, Path],
    store_path: Union[str, Path],
    state_path: Optional[Union[str, Path]] = None,
    fsync: bool = True,
    dry_run: bool = False,
) -> Dict:
    wal = Path(wal_path)
    store = Path(store_path)
    state = Path(state_path) if state_path else default_state_path(store)

    recovery_state = load_recovery_state(state)
    applied_tx_ids: Set[str] = set(recovery_state.get("applied_tx_ids", []))

    scan = recover_transactions(wal)
    applied: List[Dict] = []
    skipped: List[Dict] = []
    errors: List[Dict] = []

    for intent in scan.get("committed", []):
        payload = intent.get("payload") or {}
        tx_id = payload.get("tx_id")
        action = payload.get("action")

        if not tx_id:
            errors.append({"reason": "missing_tx_id", "intent": intent})
            continue

        if tx_id in applied_tx_ids:
            skipped.append({"tx_id": tx_id, "reason": "already_applied"})
            continue

        if action != "append_record":
            skipped.append({"tx_id": tx_id, "reason": "unsupported_action", "action": action})
            continue

        data = payload.get("data") or {}
        record_type = data.get("record_type")
        record_payload = data.get("payload")
        if not record_type or not isinstance(record_payload, dict):
            errors.append({"tx_id": tx_id, "reason": "invalid_append_record_payload"})
            continue

        if dry_run:
            applied.append({"tx_id": tx_id, "dry_run": True, "record_type": record_type})
            continue

        try:
            append_result = append_record(store, record_type, record_payload, fsync=fsync)
            applied_tx_ids.add(tx_id)
            applied.append({"tx_id": tx_id, "append_result": append_result})
        except Exception as e:
            errors.append({"tx_id": tx_id, "reason": "append_failed", "error": str(e)})

    if not dry_run:
        recovery_state["applied_tx_ids"] = sorted(applied_tx_ids)
        recovery_state["updated_ts"] = now_ms()
        recovery_state["last_recovery"] = {
            "wal_path": str(wal),
            "store_path": str(store),
            "committed_seen": scan.get("committed_count", 0),
            "pending_seen": scan.get("pending_count", 0),
            "aborted_seen": scan.get("aborted_count", 0),
            "applied_this_run": len(applied),
            "skipped_this_run": len(skipped),
            "errors_this_run": len(errors),
            "ts": now_ms(),
        }
        atomic_write_json(state, recovery_state)

    store_records = read_all_records(store) if store.exists() else []
    store_index = build_index(store_records)

    status = "PASS_V03H3_CRASH_RECOVERY" if not errors else "NO_GO_V03H3_CRASH_RECOVERY_ERRORS"
    return {
        "status": status,
        "wal_path": str(wal),
        "store_path": str(store),
        "state_path": str(state),
        "dry_run": dry_run,
        "wal_recovery": {
            "record_count": scan.get("record_count", 0),
            "committed_count": scan.get("committed_count", 0),
            "pending_count": scan.get("pending_count", 0),
            "aborted_count": scan.get("aborted_count", 0),
        },
        "applied_count": len(applied),
        "skipped_count": len(skipped),
        "error_count": len(errors),
        "applied": applied,
        "skipped": skipped,
        "errors": errors,
        "store_index": store_index,
        "recovery_state": {
            "applied_tx_ids": sorted(applied_tx_ids),
            "path": str(state),
        },
        "ts": now_ms(),
    }
