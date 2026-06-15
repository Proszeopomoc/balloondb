import hashlib
import json
import os
import time
from collections import deque
from pathlib import Path

FEATURE_VERSION = "V03G9_QUERY_HISTORY_AND_EXPLAIN_TRACE"
DEFAULT_MAX_HISTORY_ENTRIES = 1000
MAX_STRING_LENGTH = 240
MAX_DICT_ITEMS = 32
MAX_LIST_ITEMS = 32
MAX_SANITIZE_DEPTH = 5
REDACTED_VALUE = "[REDACTED]"
REDACT_KEYS = {"secret", "token", "password", "api_key", "authorization", "credential"}

CORE_DIR = Path(__file__).resolve().parent
DATA_DIR = CORE_DIR / "data"
DEFAULT_HISTORY_PATH = DATA_DIR / "query_history.jsonl"
DEFAULT_TRACE_DIR = DATA_DIR / "explain_traces"
TRACE_STAGE_NAMES = ("parse", "plan", "filter", "execute", "return")


def _now_ms():
    return int(time.time() * 1000)


def normalize_query(query_text):
    if query_text is None:
        return ""
    return " ".join(str(query_text).strip().split())


def compute_query_hash(query_text, plan_version):
    normalized = normalize_query(query_text)
    h = hashlib.sha256()
    h.update(normalized.encode("utf-8", errors="replace"))
    h.update(b"\n")
    h.update(str(plan_version).encode("utf-8", errors="replace"))
    return h.hexdigest()


def _truncate_string(value):
    text = str(value)
    if len(text) <= MAX_STRING_LENGTH:
        return text
    return text[:MAX_STRING_LENGTH] + "...[TRUNCATED]"


def _safe_key(key):
    try:
        return _truncate_string(str(key))
    except Exception:
        return "<unprintable_key>"


def sanitize_for_log(value, depth=0):
    if depth > MAX_SANITIZE_DEPTH:
        return "<max_depth_reached>"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _truncate_string(value)
    if isinstance(value, bytes):
        return "<bytes len={}>".format(len(value))
    if isinstance(value, dict):
        out = {}
        count = 0
        skipped = 0
        for key, item in value.items():
            if count >= MAX_DICT_ITEMS:
                skipped += 1
                continue
            safe_key = _safe_key(key)
            if str(key).lower() in REDACT_KEYS:
                out[safe_key] = REDACTED_VALUE
            else:
                out[safe_key] = sanitize_for_log(item, depth + 1)
            count += 1
        if skipped:
            out["__truncated_items__"] = skipped
        return out
    if isinstance(value, (list, tuple, set)):
        seq = list(value)
        out = [sanitize_for_log(item, depth + 1) for item in seq[:MAX_LIST_ITEMS]]
        if len(seq) > MAX_LIST_ITEMS:
            out.append({"__truncated_items__": len(seq) - MAX_LIST_ITEMS})
        return out
    return _truncate_string("<{}:{}>".format(type(value).__name__, value))


def _resolve_history_path(history_path):
    return Path(history_path) if history_path else DEFAULT_HISTORY_PATH


def _resolve_trace_dir(trace_dir):
    return Path(trace_dir) if trace_dir else DEFAULT_TRACE_DIR


def _enforce_bounded_history(history_path, max_entries):
    max_entries = int(max_entries or DEFAULT_MAX_HISTORY_ENTRIES)
    if max_entries < 1:
        max_entries = 1
    path = Path(history_path)
    if not path.exists():
        return
    newest = deque(maxlen=max_entries)
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.strip():
                newest.append(line.rstrip("\n"))
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for line in newest:
            f.write(line + "\n")
    os.replace(str(tmp), str(path))


def record_query_history(query_text, status, elapsed_ms, result_count, plan_version, safety_flags, extras=None, max_entries=DEFAULT_MAX_HISTORY_ENTRIES, history_path=None):
    path = _resolve_history_path(history_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    query_hash = compute_query_hash(query_text, plan_version)
    row = {
        "query_hash": query_hash,
        "timestamp": _now_ms(),
        "status": _truncate_string(status),
        "elapsed_ms": int(max(0, elapsed_ms or 0)),
        "result_count": int(max(0, result_count or 0)),
        "plan_version": _truncate_string(plan_version),
        "safety_flags": sanitize_for_log(safety_flags or {}),
        "extras": sanitize_for_log(extras or {}),
        "feature_version": FEATURE_VERSION,
        "bounded_metadata_only": True
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    _enforce_bounded_history(path, max_entries)
    return row


def _safe_trace_filename(query_hash):
    text = str(query_hash)
    safe = "".join(ch for ch in text if ch.isalnum() or ch in ("-", "_"))
    if not safe:
        safe = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
    return safe[:128] + ".json"


def _stage_record(name, started_at, finished_at, summary, diagnostics=None):
    started_at = int(started_at)
    finished_at = int(finished_at)
    if finished_at < started_at:
        finished_at = started_at
    return {
        "name": str(name),
        "started_at": started_at,
        "finished_at": finished_at,
        "elapsed_ms": finished_at - started_at,
        "summary": _truncate_string(summary),
        "diagnostics": sanitize_for_log(diagnostics or {})
    }


def build_basic_stages(status, elapsed_ms, result_count, diagnostics=None):
    total = int(max(0, elapsed_ms or 0))
    base = _now_ms() - total
    status_text = str(status or "unknown")
    diagnostics = diagnostics or {}
    stage_summaries = {
        "parse": "query accepted by parser" if status_text == "ok" else "query rejected or failed before completion",
        "plan": "read-only bounded plan metadata prepared" if status_text == "ok" else "plan skipped or failed",
        "filter": "filters evaluated within bounded query path" if status_text == "ok" else "filter skipped or failed",
        "execute": "executor completed with bounded metadata" if status_text == "ok" else "executor rejected or raised an error",
        "return": "returned_count={}".format(int(max(0, result_count or 0))) if status_text == "ok" else "no result payload persisted"
    }
    stages = []
    cursor = base
    slice_ms = max(0, total // len(TRACE_STAGE_NAMES)) if TRACE_STAGE_NAMES else 0
    for index, name in enumerate(TRACE_STAGE_NAMES):
        end = cursor + slice_ms
        if index == len(TRACE_STAGE_NAMES) - 1:
            end = base + total
        stages.append(_stage_record(name, cursor, end, stage_summaries[name], diagnostics if name in {"parse", "execute"} else {}))
        cursor = end
    return stages


def create_explain_trace(query_hash, stages, plan_version, safety_flags=None, trace_dir=None, extras=None):
    directory = _resolve_trace_dir(trace_dir)
    directory.mkdir(parents=True, exist_ok=True)
    stage_map = {}
    for item in stages or []:
        if isinstance(item, dict):
            name = str(item.get("name", ""))
            if not name:
                continue
            started = item.get("started_at", _now_ms())
            finished = item.get("finished_at", started)
            stage_map[name] = _stage_record(name, started, finished, item.get("summary", ""), item.get("diagnostics", {}))
    ordered = []
    now = _now_ms()
    for name in TRACE_STAGE_NAMES:
        ordered.append(stage_map.get(name) or _stage_record(name, now, now, "stage metadata unavailable", {}))
    doc = {
        "type": "BQL_EXPLAIN_TRACE",
        "query_hash": str(query_hash),
        "created_at": _now_ms(),
        "plan_version": _truncate_string(plan_version),
        "feature_version": FEATURE_VERSION,
        "bounded_metadata_only": True,
        "safety_flags": sanitize_for_log(safety_flags or {}),
        "extras": sanitize_for_log(extras or {}),
        "stages": ordered
    }
    path = directory / _safe_trace_filename(query_hash)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return str(path)


def _result_count(result):
    if not isinstance(result, dict):
        return 0
    balloon = result.get("balloon_expand")
    if isinstance(balloon, dict):
        if isinstance(balloon.get("returned_count"), int):
            return balloon.get("returned_count")
        if isinstance(balloon.get("results"), list):
            return len(balloon.get("results"))
    for key in ("returned_count", "result_count", "count"):
        if isinstance(result.get(key), int):
            return result.get(key)
    return 0


def _default_safety_flags(extra=None):
    flags = {
        "read_only": True,
        "no_write": True,
        "no_wal": True,
        "no_network": True,
        "no_full_graph_export": True,
        "bounded_metadata_only": True
    }
    if isinstance(extra, dict):
        flags.update(extra)
    return flags


def run_query_with_history(query_text, memory_root="memory/balloon_memory.balloondb", max_results=50, plan_version=FEATURE_VERSION, max_entries=DEFAULT_MAX_HISTORY_ENTRIES):
    start = _now_ms()
    query_hash = compute_query_hash(query_text, plan_version)
    safety = _default_safety_flags()
    try:
        from balloondb_core.bql_executor import execute
        result = execute(query_text, memory_root=memory_root, max_results=max_results)
        elapsed = _now_ms() - start
        result_count = _result_count(result)
        raw_status = result.get("status", "") if isinstance(result, dict) else ""
        if isinstance(raw_status, str) and raw_status.startswith("PASS"):
            history_row = record_query_history(query_text, "ok", elapsed, result_count, plan_version, safety, extras={"executor_status": raw_status}, max_entries=max_entries)
            trace_path = create_explain_trace(query_hash, build_basic_stages("ok", elapsed, result_count, {"executor_status": raw_status}), plan_version, safety_flags=safety, extras={"history_status": "ok"})
            if isinstance(result, dict):
                result.setdefault("query_history", {"query_hash": history_row["query_hash"], "trace_path": trace_path, "bounded_metadata_only": True})
            return result
        diagnostic_status = raw_status or "non_pass_executor_status"
        record_query_history(query_text, "error", elapsed, result_count, plan_version, safety, extras={"executor_status": diagnostic_status}, max_entries=max_entries)
        create_explain_trace(query_hash, build_basic_stages("error", elapsed, result_count, {"executor_status": diagnostic_status}), plan_version, safety_flags=safety, extras={"history_status": "error"})
        raise RuntimeError("BQL executor returned non-pass status: {}".format(diagnostic_status))
    except Exception as exc:
        elapsed = _now_ms() - start
        status = "rejected" if exc.__class__.__name__ in {"ParseError", "ValueError"} or "unsafe token rejected" in str(exc).lower() else "error"
        diagnostic = {"error_type": exc.__class__.__name__, "error": str(exc)}
        record_query_history(query_text, status, elapsed, 0, plan_version, safety, extras=diagnostic, max_entries=max_entries)
        create_explain_trace(query_hash, build_basic_stages(status, elapsed, 0, diagnostic), plan_version, safety_flags=safety, extras={"history_status": status})
        raise
