
import json
import shutil
import time
from pathlib import Path

from balloondb_core.wal_v03h2 import begin_transaction, commit_transaction, abort_transaction, read_wal_records
from balloondb_core.storage_format_v03h1 import read_all_records, build_index
from balloondb_core.crash_recovery_v03h3 import recover_database

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "balloondb_core" / "data" / "v03h3_crash_recovery_selftest"
REPORT_DIR = ROOT / "06_EVIDENCE" / "BALLOONDB_V03H3"

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

    wal = DATA / "v03h3_selftest.wal"
    store = DATA / "v03h3_recovered_store.bdb"
    state = DATA / "v03h3_recovery_state.json"

    tx1_data = {
        "record_type": "SEED",
        "payload": {
            "seed_id": "SEED_CRASH_COMMITTED_1",
            "seed_type": "CRASH_TEST",
            "status": "OBSERVED",
            "data": {"route": "commit_before_crash"}
        }
    }
    tx2_data = {
        "record_type": "BRIDGE",
        "payload": {
            "bridge_id": "BRIDGE_CRASH_COMMITTED_2",
            "from_seed": "SEED_CRASH_COMMITTED_1",
            "to_seed": "SEED_CRASH_TARGET",
            "bridge_type": "RECOVERS",
            "status": "OBSERVED",
            "data": {"route": "second_commit"}
        }
    }
    tx3_data = {
        "record_type": "SEED",
        "payload": {
            "seed_id": "SEED_CRASH_PENDING",
            "seed_type": "CRASH_TEST",
            "status": "OBSERVED",
            "data": {"route": "pending_should_not_apply"}
        }
    }
    tx4_data = {
        "record_type": "SEED",
        "payload": {
            "seed_id": "SEED_CRASH_ABORTED",
            "seed_type": "CRASH_TEST",
            "status": "OBSERVED",
            "data": {"route": "aborted_should_not_apply"}
        }
    }

    # WAL layout:
    # TX1 committed -> should apply
    # TX2 committed -> should apply
    # TX3 pending -> should not apply
    # TX4 aborted -> should not apply
    begin_transaction(wal, "TX_CRASH_COMMITTED_1", "append_record", tx1_data, target_path=str(store))
    commit_transaction(wal, "TX_CRASH_COMMITTED_1")
    begin_transaction(wal, "TX_CRASH_COMMITTED_2", "append_record", tx2_data, target_path=str(store))
    commit_transaction(wal, "TX_CRASH_COMMITTED_2")
    begin_transaction(wal, "TX_CRASH_PENDING_1", "append_record", tx3_data, target_path=str(store))
    begin_transaction(wal, "TX_CRASH_ABORTED_1", "append_record", tx4_data, target_path=str(store))
    abort_transaction(wal, "TX_CRASH_ABORTED_1", reason="selftest_abort")

    first = recover_database(wal, store, state_path=state)
    second = recover_database(wal, store, state_path=state)

    store_records = read_all_records(store)
    idx = build_index(store_records)

    checks = {}
    checks["first_recovery_pass"] = first["status"] == "PASS_V03H3_CRASH_RECOVERY"
    checks["first_applied_two"] = first["applied_count"] == 2
    checks["second_idempotent_zero_applied"] = second["applied_count"] == 0 and second["skipped_count"] == 2
    checks["store_total_two"] = idx["total"] == 2
    checks["committed_seed_present"] = "SEED_CRASH_COMMITTED_1" in idx["seed_ids"]
    checks["committed_bridge_present"] = "BRIDGE_CRASH_COMMITTED_2" in idx["bridge_ids"]
    checks["pending_absent"] = "SEED_CRASH_PENDING" not in idx["seed_ids"]
    checks["aborted_absent"] = "SEED_CRASH_ABORTED" not in idx["seed_ids"]

    partial_wal = DATA / "v03h3_partial_tail.wal"
    partial_wal.write_bytes(wal.read_bytes()[:-11])
    partial_store = DATA / "v03h3_partial_store.bdb"
    partial_state = DATA / "v03h3_partial_state.json"
    partial = recover_database(partial_wal, partial_store, state_path=partial_state)
    checks["partial_tail_recovery_pass"] = partial["status"] == "PASS_V03H3_CRASH_RECOVERY"
    checks["partial_tail_applies_only_complete_commits"] = partial["applied_count"] == 2

    status = "PASS_V03H3_CRASH_RECOVERY_SELFTEST" if all(checks.values()) else "NO_GO_V03H3_CRASH_RECOVERY_SELFTEST"
    report = {
        "status": status,
        "version": "BALLOONDB_V03H3_CRASH_RECOVERY_LOCAL_IMPLEMENTATION",
        "wal": str(wal),
        "store": str(store),
        "state": str(state),
        "first_recovery": first,
        "second_recovery": second,
        "partial_tail_recovery": partial,
        "store_index": idx,
        "checks": checks,
        "safety": {
            "no_network": True,
            "no_openai": True,
            "no_lmstudio": True,
            "sandbox_data_dir": str(DATA),
            "production_memory_unchanged": True
        },
        "ts": now_ms(),
    }
    report["report"] = write_json(REPORT_DIR / f"V03H3_CRASH_RECOVERY_SELFTEST_REPORT_{now_ms()}.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if status.startswith("PASS") else 3

if __name__ == "__main__":
    raise SystemExit(main())
