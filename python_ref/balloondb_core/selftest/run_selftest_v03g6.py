import json
import time
from pathlib import Path

from balloondb_core.bql_parser import parse, ParseError
from balloondb_core.bql_planner import explain
from balloondb_core.bql_executor import execute
from balloondb_core.bql_time_filter import parse_ts_filter, match_ts_filter, record_ts

DATA = Path("balloondb_core") / "data"
REPORTS = Path("balloondb_core") / "reports"
MEMORY = DATA / "v03g6_time_filter_memory.balloondb"

def _write_memory(now_ms):
    MEMORY.mkdir(parents=True, exist_ok=True)
    pack = MEMORY / "time_records.jsonl"
    rows = [
        {"id": "recent", "seed": "TIME_SEED", "concept": "RECENT", "summary": "inside last hour", "ts": now_ms - 30 * 60 * 1000, "depth": 1},
        {"id": "older", "seed": "TIME_SEED", "concept": "OLDER", "summary": "outside last hour", "ts": now_ms - 2 * 60 * 60 * 1000, "depth": 1},
        {"id": "week_old", "seed": "TIME_SEED", "concept": "WEEK_OLD", "summary": "outside last seven days", "ts": now_ms - 8 * 24 * 60 * 60 * 1000, "depth": 1},
        {"id": "missing_ts", "seed": "TIME_SEED", "concept": "NO_TS", "summary": "missing timestamp", "depth": 1}
    ]
    with pack.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return pack

def run_selftest(memory_root=None):
    DATA.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    now_ms = int(time.time() * 1000)
    pack = _write_memory(now_ms)
    root = str(memory_root or MEMORY)

    cases = []

    f1 = parse_ts_filter("ts > 1700000000000")
    cases.append({"name": "parse_ts_greater", "pass": f1 == {"field": "ts", "op": ">", "value": 1700000000000}, "value": f1})

    f2 = parse_ts_filter("ts IN last_hour")
    cases.append({"name": "parse_ts_named_window", "pass": f2 == {"field": "ts", "op": "in_window", "window": "last_hour"}, "value": f2})

    cases.append({"name": "record_ts_missing_returns_none", "pass": record_ts({"x": 1}) is None})
    cases.append({"name": "match_last_hour_inclusive", "pass": match_ts_filter(now_ms - 60 * 60 * 1000, f2, now_ms=now_ms) is True})
    cases.append({"name": "match_future_rejected", "pass": match_ts_filter(now_ms + 1, f2, now_ms=now_ms) is False})

    try:
        parse_ts_filter("ts >= 1700000000000")
        bad_op = False
    except Exception as exc:
        bad_op = "unsupported timestamp operator" in str(exc)
    cases.append({"name": "reject_unsupported_ts_operator", "pass": bad_op})

    try:
        parse('FROM seed("TIME_SEED") BALLOON radius=4 direction=up_down RETURN concept')
        bad_radius = False
    except ParseError as exc:
        bad_radius = "allowed 1..3" in str(exc)
    cases.append({"name": "reject_radius_above_three", "pass": bad_radius})

    ast = parse('FROM seed("TIME_SEED") BALLOON radius=2 direction=up_down FILTER ts IN last_hour RETURN concept,ts TOP 10')
    plan = explain(ast)
    cases.append({"name": "planner_time_filter_metadata", "pass": plan.get("version") == "V03G6_BQL_TIME_FILTER" and any(step.get("time_filter") is True for step in plan.get("steps", [])), "plan_version": plan.get("version")})

    result = execute('FROM seed("TIME_SEED") BALLOON radius=2 direction=up_down FILTER ts IN last_hour RETURN concept,ts TOP 10', memory_root=root, max_results=50)
    concepts = [row.get("concept") for row in result.get("balloon_expand", {}).get("results", [])]
    cases.append({"name": "execute_last_hour_filters_records", "pass": "RECENT" in concepts and "OLDER" not in concepts and "NO_TS" not in concepts, "concepts": concepts, "status": result.get("status")})

    result_gt = execute(f'FROM seed("TIME_SEED") BALLOON radius=2 direction=up_down FILTER ts > {now_ms - 60 * 60 * 1000} RETURN concept,ts TOP 10', memory_root=root, max_results=50)
    concepts_gt = [row.get("concept") for row in result_gt.get("balloon_expand", {}).get("results", [])]
    cases.append({"name": "execute_ts_greater_filter", "pass": "RECENT" in concepts_gt and "OLDER" not in concepts_gt, "concepts": concepts_gt})

    status = "PASS_V03G6_BQL_TIME_FILTER_SELFTEST" if all(c.get("pass") for c in cases) else "FAIL_V03G6_BQL_TIME_FILTER_SELFTEST"
    output = {
        "status": status,
        "version": "V03G6_BQL_TIME_FILTER",
        "cases": cases,
        "memory_root": root,
        "pack": str(pack),
        "safety": {
            "read_only_executor": True,
            "no_write_from_executor": True,
            "no_wal": True,
            "no_vector_engine": True,
            "no_network": True,
            "max_radius": 3
        },
        "ts": int(time.time() * 1000)
    }
    out_path = DATA / "v03g6_selftest_output.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    output["output"] = str(out_path)
    return output

if __name__ == "__main__":
    print(json.dumps(run_selftest(), ensure_ascii=False, indent=2))
