
import json
import shutil
import time
from pathlib import Path

from balloondb_core.wal_v03h2 import (
    begin_transaction,
    commit_transaction,
    abort_transaction,
    read_wal_records,
    recover_transactions,
    apply_committed_append_records,
    BalloonWALError,
)
from balloondb_core.storage_format_v03h1 import read_all_records, build_index

ROOT = Path(r"C:\BalloonOperator")
DATA = ROOT / "balloondb_core" / "data" / "v03h2_wal_selftest"
REPORT_DIR = ROOT / "06_EVIDENCE" / "BALLOONDB_V03H2"

def now_ms():
    return int(time.time() * 1000)

def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)

def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if DATA.exists():
        shutil.rmtree(DATA)
    DATA.mkdir(parents=True, exist_ok=True)

    wal = DATA / "v03h2_selftest.wal"
    store = DATA / "v03h2_recovered_store.bdb"

    tx1_data = {
        "record_type": "SEED",
        "payload": {
            "seed_id": "SEED_WAL_COMMITTED",
            "seed_type": "WAL_TEST",
            "status": "OBSERVED",
            "data": {"source": "committed_tx"}
        }
    }
    tx2_data = {
        "record_type": "SEED",
        "payload": {
            "seed_id": "SEED_WAL_PENDING",
            "seed_type": "WAL_TEST",
            "status": "OBSERVED",
            "data": {"source": "pending_tx"}
        }
    }
    tx3_data = {
        "record_type": "SEED",
        "payload": {
            "seed_id": "SEED_WAL_ABORTED",
            "seed_type": "WAL_TEST",
            "status": "OBSERVED",
            "data": {"source": "aborted_tx"}
        }
    }

    a1 = begin_transaction(wal, "TX_COMMITTED_1", "append_record", tx1_data, target_path=str(store))
    a2 = commit_transaction(wal, "TX_COMMITTED_1")
    a3 = begin_transaction(wal, "TX_PENDING_1", "append_record", tx2_data, target_path=str(store))
    a4 = begin_transaction(wal, "TX_ABORTED_1", "append_record", tx3_data, target_path=str(store))
    a5 = abort_transaction(wal, "TX_ABORTED_1", reason="selftest_abort")

    records = read_wal_records(wal)
    recovery = recover_transactions(wal)
    applied = apply_committed_append_records(wal, store)
    store_records = read_all_records(store)
    idx = build_index(store_records)

    checks = {}
    checks["wal_record_count_5"] = len(records) == 5
    checks["seq_monotonic"] = [r["seq"] for r in records] == [1, 2, 3, 4, 5]
    checks["checksums_ok"] = all(r["checksum_ok"] for r in records)
    checks["recovery_counts"] = recovery["committed_count"] == 1 and recovery["pending_count"] == 1 and recovery["aborted_count"] == 1
    checks["apply_only_committed"] = applied["applied_count"] == 1 and len(store_records) == 1
    checks["store_has_committed_seed"] = "SEED_WAL_COMMITTED" in idx["seed_ids"]
    checks["store_excludes_pending_seed"] = "SEED_WAL_PENDING" not in idx["seed_ids"]
    checks["store_excludes_aborted_seed"] = "SEED_WAL_ABORTED" not in idx["seed_ids"]

    partial = DATA / "partial_copy.wal"
    partial.write_bytes(wal.read_bytes()[:-9])
    partial_recovery = recover_transactions(partial)
    checks["partial_tail_stops_cleanly"] = partial_recovery["record_count"] == 4

    status = "PASS_V03H2_APPEND_ONLY_WAL_SELFTEST" if all(checks.values()) else "NO_GO_V03H2_APPEND_ONLY_WAL_SELFTEST"
    report = {
        "status": status,
        "version": "BALLOONDB_V03H2_APPEND_ONLY_WAL_LOCAL_IMPLEMENTATION",
        "wal": str(wal),
        "store": str(store),
        "append_results": [a1, a2, a3, a4, a5],
        "recovery": {
            "record_count": recovery["record_count"],
            "committed_count": recovery["committed_count"],
            "pending_count": recovery["pending_count"],
            "aborted_count": recovery["aborted_count"],
        },
        "applied": applied,
        "store_index": idx,
        "checks": checks,
        "safety": {
            "no_network": True,
            "no_openai": True,
            "no_lmstudio": True,
            "sandbox_data_dir": str(DATA),
            "production_memory_unchanged": True,
        },
        "ts": now_ms(),
    }
    report["report"] = write_json(REPORT_DIR / f"V03H2_APPEND_ONLY_WAL_SELFTEST_REPORT_{now_ms()}.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if status.startswith("PASS") else 3

if __name__ == "__main__":
    raise SystemExit(main())
