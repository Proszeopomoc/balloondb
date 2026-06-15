import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from balloondb_core.bql_executor import execute
from balloondb_core import bql_ts_index


def _write_jsonl(path, rows):
    with Path(path).open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _result_rows(result):
    return result.get("balloon_expand", {}).get("results", [])


def _assert_equal_results(indexed, full_scan):
    left = _result_rows(indexed)
    right = _result_rows(full_scan)
    if left != right:
        raise AssertionError("indexed results differ from full scan: " + json.dumps({"indexed": left, "full_scan": right}, ensure_ascii=False))


def run_selftest():
    now = int(time.time() * 1000)
    rows = [
        {"record_id": "old_out_of_range", "seed": "V03G8_SEED", "concept": "demo", "label": "old", "ts": now - (3 * 60 * 60 * 1000)},
        {"record_id": "recent_one", "seed": "V03G8_SEED", "concept": "demo", "label": "recent", "ts": now - 30_000},
        {"record_id": "recent_two", "seed": "V03G8_SEED", "concept": "demo", "label": "recent", "ts": str(now - 10_000)},
        {"record_id": "invalid_ts", "seed": "V03G8_SEED", "concept": "demo", "label": "bad", "ts": "not-a-timestamp"},
        {"record_id": "missing_ts", "seed": "V03G8_SEED", "concept": "demo", "label": "missing"},
        {"record_id": "other_seed", "seed": "OTHER_SEED", "concept": "demo", "label": "other", "ts": now - 5_000}
    ]

    cases = []
    with tempfile.TemporaryDirectory(prefix="v03g8_ts_index_") as tmp:
        tmp_path = Path(tmp)
        memory_path = tmp_path / "memory.jsonl"
        _write_jsonl(memory_path, rows)
        before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))

        threshold = now - (60 * 60 * 1000)
        q_gt = f'FROM seed("V03G8_SEED") BALLOON radius=1 direction=up_down FILTER ts > {threshold} RETURN record_id,ts,label TOP 20'
        q_window = 'FROM seed("V03G8_SEED") BALLOON radius=1 direction=up_down FILTER ts IN last_hour RETURN record_id,ts,label TOP 20'

        idx_gt = execute(q_gt, memory_root=str(memory_path), max_results=20, use_ts_index=True)
        scan_gt = execute(q_gt, memory_root=str(memory_path), max_results=20, use_ts_index=False)
        _assert_equal_results(idx_gt, scan_gt)

        idx_window = execute(q_window, memory_root=str(memory_path), max_results=20, use_ts_index=True)
        scan_window = execute(q_window, memory_root=str(memory_path), max_results=20, use_ts_index=False)
        _assert_equal_results(idx_window, scan_window)

        direct_index = bql_ts_index.build_index_from_jsonl(memory_path)
        direct_refs = bql_ts_index.refs_for_filters(direct_index, [{"field": "ts", "op": ">", "value": threshold}])
        direct_rows = bql_ts_index.resolve_jsonl_refs(memory_path, direct_refs)

        after = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
        created = sorted(set(after) - set(before))
        bad_created = [name for name in created if name.lower().endswith(".wal") or "tsindex" in name.lower() or name.lower().endswith(".idx")]

        cases.append({"name": "gt_indexed_equals_full_scan", "pass": _result_rows(idx_gt) == _result_rows(scan_gt)})
        cases.append({"name": "window_indexed_equals_full_scan", "pass": _result_rows(idx_window) == _result_rows(scan_window)})
        cases.append({"name": "plan_metadata_present", "pass": all(k in idx_gt.get("plan", {}) for k in ("ts_index_candidate", "ts_index_used", "ts_index_reason"))})
        cases.append({"name": "plan_index_used_true", "pass": idx_gt.get("plan", {}).get("ts_index_candidate") is True and idx_gt.get("plan", {}).get("ts_index_used") is True})
        cases.append({"name": "full_scan_index_used_false", "pass": scan_gt.get("plan", {}).get("ts_index_used") is False})
        cases.append({"name": "invalid_and_missing_timestamps_skipped", "pass": all(row.get("record_id") not in {"invalid_ts", "missing_ts"} for row in direct_rows)})
        cases.append({"name": "read_only_no_persisted_index_or_wal", "pass": not bad_created, "created": created})
        cases.append({"name": "safety_no_write", "pass": idx_gt.get("safety", {}).get("no_write") is True and idx_gt.get("safety", {}).get("no_wal") is True})

    status = "PASS_V03G8_TS_INDEX_SELFTEST" if all(case["pass"] for case in cases) else "FAIL_V03G8_TS_INDEX_SELFTEST"
    return {
        "status": status,
        "feature_id": "V03G8_TS_INDEX_FOR_TIME_FILTER",
        "cases": cases,
        "ts": int(time.time() * 1000)
    }


if __name__ == "__main__":
    result = run_selftest()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.get("status") == "PASS_V03G8_TS_INDEX_SELFTEST" else 3)
