import html
import json
import sys
import time
from pathlib import Path

from balloondb_core import bql_query_history as qh

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "balloondb_core"
DATA = CORE / "data"
EVIDENCE = ROOT / "06_EVIDENCE" / "BALLOONDB_BQL_CORE"
REPORTS = CORE / "reports"
HISTORY_PATH = DATA / "query_history.jsonl"
TRACE_DIR = DATA / "explain_traces"
SELFTEST_PLAN_VERSION = "V03G9_SELFTEST_QUERY_HISTORY_AND_EXPLAIN_TRACE"


def _now_ms():
    return int(time.time() * 1000)


def _rel(path):
    try:
        return str(Path(path).resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def _load_jsonl(path):
    rows = []
    p = Path(path)
    if not p.exists():
        return rows
    with p.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_json(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return p


def _create_test_memory():
    DATA.mkdir(parents=True, exist_ok=True)
    memory_dir = DATA / "selftest_v03g9_memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "record_id": "V03G9_SEED",
            "id": "V03G9_SEED",
            "concept": "V03G9_HISTORY_ROOT",
            "evidence": "safe local selftest evidence root",
            "summary": "bounded metadata selftest root",
            "pack": "selftest_v03g9",
            "depth": 0,
            "parent_id": "",
            "neighbors": ["V03G9_CHILD"]
        },
        {
            "record_id": "V03G9_CHILD",
            "id": "V03G9_CHILD",
            "concept": "V03G9_HISTORY_CHILD",
            "evidence": "safe local selftest evidence child",
            "summary": "bounded metadata selftest child",
            "pack": "selftest_v03g9",
            "depth": 1,
            "parent_id": "V03G9_SEED",
            "neighbors": []
        }
    ]
    jsonl_text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    (memory_dir / "pack_selftest_v03g9.jsonl").write_text(jsonl_text, encoding="utf-8")
    memory_file = DATA / "selftest_v03g9_memory.jsonl"
    memory_file.write_text(jsonl_text, encoding="utf-8")
    return memory_dir, memory_file


def _trace_path(query_hash):
    return TRACE_DIR / (query_hash + ".json")


def _has_forbidden_payload_key(value):
    forbidden = {"raw_query", "query_text", "full_query", "raw_results", "result_set", "graph_payload", "full_graph", "payload"}
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) in forbidden:
                return True
            if _has_forbidden_payload_key(item):
                return True
    elif isinstance(value, list):
        for item in value:
            if _has_forbidden_payload_key(item):
                return True
    return False


def _validate_trace(query_hash):
    path = _trace_path(query_hash)
    if not path.exists():
        return False, "missing trace file: " + _rel(path)
    doc = json.loads(path.read_text(encoding="utf-8"))
    stages = doc.get("stages", [])
    names = [stage.get("name") for stage in stages if isinstance(stage, dict)]
    required = ["parse", "plan", "filter", "execute", "return"]
    if names != required:
        return False, "trace stage order mismatch: " + repr(names)
    for stage in stages:
        for key in ["name", "started_at", "finished_at", "elapsed_ms", "summary", "diagnostics"]:
            if key not in stage:
                return False, "trace stage missing key: " + key
    if _has_forbidden_payload_key(doc):
        return False, "trace contains forbidden raw payload key"
    return True, "trace schema valid"


def _case(name, passed, detail=""):
    return {"name": name, "pass": bool(passed), "detail": str(detail)}


def run_selftest():
    DATA.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    TRACE_DIR.mkdir(parents=True, exist_ok=True)

    cases = []
    started = _now_ms()
    memory_dir, memory_file = _create_test_memory()
    cases.append(_case("local_test_memory_created", memory_dir.exists() and memory_file.exists(), _rel(memory_dir)))

    valid_query = 'FROM seed("V03G9_SEED") BALLOON radius=1 direction=up_down RETURN concept,evidence TOP 5'
    unsafe_query = 'DELETE FROM seed("V03G9_SEED") BALLOON radius=1 direction=up_down RETURN concept'

    valid_ok = False
    valid_detail = ""
    try:
        result = qh.run_query_with_history(valid_query, memory_root=str(memory_dir), max_results=5, plan_version=SELFTEST_PLAN_VERSION, max_entries=1000)
        valid_ok = isinstance(result, dict) and str(result.get("status", "")).startswith("PASS")
        valid_detail = str(result.get("status", "")) if isinstance(result, dict) else "non_dict_result"
    except Exception as exc:
        valid_detail = exc.__class__.__name__ + ": " + str(exc)
    cases.append(_case("valid_query_recorded_through_wrapper", valid_ok, valid_detail))

    rejected_ok = False
    rejected_detail = ""
    try:
        qh.run_query_with_history(unsafe_query, memory_root=str(memory_dir), max_results=5, plan_version=SELFTEST_PLAN_VERSION, max_entries=1000)
        rejected_detail = "unsafe query unexpectedly completed"
    except Exception as exc:
        rejected_ok = "unsafe token rejected" in str(exc).lower() or exc.__class__.__name__ in {"ParseError", "RuntimeError", "ValueError"}
        rejected_detail = exc.__class__.__name__ + ": " + str(exc)
    cases.append(_case("unsafe_query_rejected_and_recorded", rejected_ok, rejected_detail))

    controlled_secret = "open-sesame-v03g9"
    controlled_token = "token-value-v03g9"
    controlled_secret2 = "hidden-secret-v03g9"
    long_value = "L" * (qh.MAX_STRING_LENGTH + 120)
    controlled_extras = {
        "password": controlled_secret,
        "nested": {"token": controlled_token, "secret": controlled_secret2},
        "long_string": long_value,
        "note": "safe controlled metadata"
    }
    controlled_query = 'FROM seed("V03G9_REDACTION") BALLOON radius=1 direction=up_down RETURN concept TOP 1'
    controlled_row = qh.record_query_history(controlled_query, "ok", 7, 0, SELFTEST_PLAN_VERSION, {"no_network": True}, extras=controlled_extras, max_entries=1000)
    qh.create_explain_trace(controlled_row["query_hash"], qh.build_basic_stages("ok", 7, 0, controlled_extras), SELFTEST_PLAN_VERSION, safety_flags={"no_network": True}, extras=controlled_extras)
    cases.append(_case("controlled_redaction_row_recorded", bool(controlled_row.get("query_hash")), controlled_row.get("query_hash", "")))

    rows = [row for row in _load_jsonl(HISTORY_PATH) if row.get("plan_version") == SELFTEST_PLAN_VERSION]
    new_rows = [row for row in rows if int(row.get("timestamp", 0)) >= started - 1000]
    cases.append(_case("at_least_two_new_history_rows", len(new_rows) >= 2, "new_rows={}".format(len(new_rows))))

    required_history_keys = {"query_hash", "timestamp", "status", "elapsed_ms", "result_count", "plan_version", "safety_flags", "feature_version"}
    schema_ok = bool(new_rows) and all(required_history_keys.issubset(set(row.keys())) for row in new_rows)
    cases.append(_case("history_required_schema", schema_ok, "required=" + ",".join(sorted(required_history_keys))))

    statuses = {str(row.get("status")) for row in new_rows}
    status_ok = "ok" in statuses and ("rejected" in statuses or "error" in statuses)
    cases.append(_case("history_statuses_include_ok_and_rejected_or_error", status_ok, ",".join(sorted(statuses))))

    trace_results = []
    for row in new_rows:
        ok, detail = _validate_trace(row.get("query_hash", ""))
        trace_results.append({"query_hash": row.get("query_hash", ""), "pass": ok, "detail": detail})
    cases.append(_case("matching_trace_files_and_stage_schema", bool(trace_results) and all(item["pass"] for item in trace_results), json.dumps(trace_results, ensure_ascii=False)))

    controlled_history_text = HISTORY_PATH.read_text(encoding="utf-8", errors="replace") if HISTORY_PATH.exists() else ""
    controlled_trace_text = _trace_path(controlled_row["query_hash"]).read_text(encoding="utf-8", errors="replace")
    combined_text = controlled_history_text + "\n" + controlled_trace_text
    redaction_ok = ("[REDACTED]" in combined_text and controlled_secret not in combined_text and controlled_token not in combined_text and controlled_secret2 not in combined_text)
    cases.append(_case("redaction_applied_to_history_and_trace", redaction_ok, "redacted_marker_present={}".format("[REDACTED]" in combined_text)))

    controlled_history_rows = [row for row in _load_jsonl(HISTORY_PATH) if row.get("query_hash") == controlled_row["query_hash"]]
    persisted_long = ""
    if controlled_history_rows:
        persisted_long = controlled_history_rows[-1].get("extras", {}).get("long_string", "")
    truncation_ok = isinstance(persisted_long, str) and len(persisted_long) <= qh.MAX_STRING_LENGTH + len("...[TRUNCATED]") and long_value not in combined_text and "[TRUNCATED]" in persisted_long
    cases.append(_case("long_metadata_truncated", truncation_ok, "persisted_length={}".format(len(persisted_long) if isinstance(persisted_long, str) else -1)))

    rotation_dir = DATA / "selftest_v03g9_rotation"
    rotation_dir.mkdir(parents=True, exist_ok=True)
    rotation_path = rotation_dir / "query_history_rotation.jsonl"
    if rotation_path.exists():
        rotation_path.unlink()
    for index in range(8):
        qh.record_query_history('FROM seed("ROT{}") BALLOON radius=1 direction=up_down RETURN concept TOP 1'.format(index), "ok", index, index, SELFTEST_PLAN_VERSION + "_ROTATION", {"no_network": True}, extras={"rotation_index": index}, max_entries=3, history_path=rotation_path)
    rotation_rows = _load_jsonl(rotation_path)
    rotation_indexes = [row.get("extras", {}).get("rotation_index") for row in rotation_rows]
    rotation_ok = len(rotation_rows) == 3 and rotation_indexes == [5, 6, 7]
    cases.append(_case("bounded_history_rotation_keeps_newest_n", rotation_ok, "indexes=" + repr(rotation_indexes)))

    pass_count = sum(1 for item in cases if item["pass"])
    fail_count = len(cases) - pass_count
    status = "PASS_V03G9_QUERY_HISTORY_AND_EXPLAIN_TRACE_SELFTEST" if fail_count == 0 else "FAIL_V03G9_QUERY_HISTORY_AND_EXPLAIN_TRACE_SELFTEST"

    report = {
        "status": status,
        "feature_id": qh.FEATURE_VERSION,
        "plan_version": SELFTEST_PLAN_VERSION,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "cases": cases,
        "history_path": _rel(HISTORY_PATH),
        "trace_dir": _rel(TRACE_DIR),
        "test_memory_dir": _rel(memory_dir),
        "test_memory_file": _rel(memory_file),
        "rotation_history_path": _rel(rotation_path),
        "trace_results": trace_results,
        "bounded_metadata_only": True,
        "ts": _now_ms()
    }

    evidence_path = _write_json(EVIDENCE / "V03G9_SELFTEST_REPORT.json", report)
    report["evidence_report"] = _rel(evidence_path)

    html_rows = "\n".join("<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(html.escape(item["name"]), html.escape("PASS" if item["pass"] else "FAIL"), html.escape(item["detail"][:500])) for item in cases)
    html_doc = "<!doctype html><html><head><meta charset=\"utf-8\"><title>V03G9 Selftest</title></head><body><h1>{}</h1><p>pass_count={} fail_count={}</p><table border=\"1\" cellpadding=\"6\"><tr><th>Case</th><th>Status</th><th>Sanitized Detail</th></tr>{}</table></body></html>".format(html.escape(status), pass_count, fail_count, html_rows)
    html_path = REPORTS / "selftest_v03g9_report.html"
    html_path.write_text(html_doc, encoding="utf-8")
    report["html_report"] = _rel(html_path)
    _write_json(evidence_path, report)
    return report


def main():
    result = run_selftest()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status") == "PASS_V03G9_QUERY_HISTORY_AND_EXPLAIN_TRACE_SELFTEST" else 3


if __name__ == "__main__":
    raise SystemExit(main())
