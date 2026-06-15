
import json
import shutil
import time
from pathlib import Path

from balloondb_core.storage_format_v03h1 import (
    create_seed,
    create_bridge,
    create_route,
    create_result,
    read_all_records,
    build_index,
    append_record,
    BalloonStorageError,
)

ROOT = Path(r"C:\BalloonOperator")
DATA = ROOT / "balloondb_core" / "data" / "v03h1_selftest"
REPORT_DIR = ROOT / "06_EVIDENCE" / "BALLOONDB_V03H1"

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
    store = DATA / "v03h1_selftest.bdb"

    checks = {}

    a1 = create_seed(store, "SEED_PROJECT_ROOT", "PROJECT", {"name": "BalloonDB", "purpose": "native storage selftest"}, status="OBSERVED")
    a2 = create_seed(store, "SEED_AGENT_ROOT", "AGENT", {"name": "Operator", "role": "local coding loop"}, status="OBSERVED")
    a3 = create_bridge(store, "BRIDGE_PROJECT_AGENT", "SEED_PROJECT_ROOT", "SEED_AGENT_ROOT", "USES", {"reason": "operator uses db memory"})
    a4 = create_route(store, "ROUTE_LOCAL_FIRST", [{"step": "recall"}, {"step": "local_model"}, {"step": "compile_selftest"}])
    a5 = create_result(store, "RESULT_V03H1_SELFTEST", "PASS", {"records_expected": 5})

    records = read_all_records(store)
    idx = build_index(records)

    checks["append_count_5"] = len(records) == 5
    checks["index_seed_count_2"] = len(idx["seed_ids"]) == 2
    checks["index_bridge_count_1"] = len(idx["bridge_ids"]) == 1
    checks["record_types_present"] = idx["by_type"].get("SEED") == 2 and idx["by_type"].get("BRIDGE") == 1 and idx["by_type"].get("ROUTE") == 1 and idx["by_type"].get("RESULT") == 1
    checks["checksums_ok"] = all(r["checksum_ok"] for r in records)

    partial = DATA / "partial_copy.bdb"
    partial.write_bytes(store.read_bytes()[:-7])
    partial_records = read_all_records(partial)
    checks["partial_tail_stops_cleanly"] = len(partial_records) == 4

    bad_payload = {"seed_id": "BAD_NO_TYPE"}
    try:
        append_record(DATA / "bad.bdb", "SEED", bad_payload)
        checks["payload_validation_rejects_bad_seed"] = False
    except BalloonStorageError:
        checks["payload_validation_rejects_bad_seed"] = True

    report = {
        "status": "PASS_V03H1_NATIVE_STORAGE_SELFTEST" if all(checks.values()) else "NO_GO_V03H1_NATIVE_STORAGE_SELFTEST",
        "version": "BALLOONDB_V03H1_NATIVE_STORAGE_LOCAL_IMPLEMENTATION",
        "store": str(store),
        "append_results": [a1, a2, a3, a4, a5],
        "index": idx,
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
    report["report"] = write_json(REPORT_DIR / f"V03H1_NATIVE_STORAGE_SELFTEST_REPORT_{now_ms()}.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"].startswith("PASS") else 3

if __name__ == "__main__":
    raise SystemExit(main())
