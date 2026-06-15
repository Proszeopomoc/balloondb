from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Iterable, List

from .bql_parser import parse
from .bql_planner import explain
from . import bql_ts_index


def _load_json_file(path: Path) -> List[dict]:
    records = []
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8-sig") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if isinstance(obj, dict):
                    records.append(obj)
        return records

    with path.open("r", encoding="utf-8-sig") as fh:
        try:
            obj = json.load(fh)
        except Exception:
            return records
    if isinstance(obj, list):
        records.extend(x for x in obj if isinstance(x, dict))
    elif isinstance(obj, dict):
        for key in ("records", "items", "data", "rows"):
            if isinstance(obj.get(key), list):
                records.extend(x for x in obj[key] if isinstance(x, dict))
                return records
        records.append(obj)
    return records


def _load_memory_records(memory_root: Any) -> List[dict]:
    root = Path(memory_root)
    if not root.exists():
        return []
    if root.is_file():
        return _load_json_file(root)

    records = []
    for suffix in ("*.jsonl", "*.json"):
        for path in sorted(root.rglob(suffix)):
            lowered = path.name.lower()
            if lowered.endswith(".wal") or "tsindex" in lowered or lowered.endswith(".idx"):
                continue
            records.extend(_load_json_file(path))
    return records


def load_memory(memory_root):
    return _load_memory_records(memory_root)


def _source_values(record: dict, kind: str) -> Iterable[Any]:
    if kind == "seed":
        keys = ("seed", "seed_id", "source", "source_value", "pattern_id", "record_id", "id")
    else:
        keys = ("concept", "concept_id", "concept_name", "pattern_id", "record_id", "id")
    for key in keys:
        if key in record:
            yield record.get(key)


def _matches_source(record: dict, source: dict) -> bool:
    wanted = str(source.get("value", ""))
    kind = source.get("kind", "seed")
    return any(str(value) == wanted for value in _source_values(record, kind))


def _expand_balloon(records: List[dict], ast: dict) -> List[dict]:
    source = ast.get("source", {})
    expanded = []
    for pos, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        if not _matches_source(record, source):
            continue
        row = dict(record)
        row.setdefault("record_id", row.get("id", pos))
        row.setdefault("depth", 0)
        row.setdefault("rank", len(expanded) + 1)
        expanded.append(row)
    return expanded


def _match_time_filter(record: dict, filt: dict) -> bool:
    ts = bql_ts_index.parse_ts_ms(record.get("ts"))
    if ts is None:
        return False
    op = filt.get("op")
    if op == ">":
        rhs = bql_ts_index.parse_ts_ms(filt.get("value"))
        return rhs is not None and ts > rhs
    if op == "<":
        rhs = bql_ts_index.parse_ts_ms(filt.get("value"))
        return rhs is not None and ts < rhs
    if op == "in_window" and filt.get("window") == "last_hour":
        return ts > int(time.time() * 1000) - bql_ts_index.LAST_HOUR_MS
    return False


def _match_filter(record: dict, filt: dict) -> bool:
    if not isinstance(filt, dict):
        return True
    if filt.get("field") == "ts":
        return _match_time_filter(record, filt)
    field = filt.get("field")
    op = filt.get("op")
    if op == "=":
        return record.get(field) == filt.get("value") or str(record.get(field)) == str(filt.get("value"))
    if op == ">":
        try:
            return float(record.get(field)) > float(filt.get("value"))
        except Exception:
            return False
    if op == "<":
        try:
            return float(record.get(field)) < float(filt.get("value"))
        except Exception:
            return False
    return False


def _apply_filters(records: List[dict], filters: List[dict]) -> List[dict]:
    if not filters:
        return list(records)
    out = []
    for record in records:
        if all(_match_filter(record, filt) for filt in filters):
            out.append(record)
    return out


def _project(records: List[dict], fields: List[str], limit: int) -> List[dict]:
    out = []
    for record in records[:limit]:
        if fields:
            row = {field: record.get(field) for field in fields}
            for extra in ("rank", "depth", "record_id"):
                if extra in record and extra not in row:
                    row[extra] = record.get(extra)
        else:
            row = dict(record)
        out.append(row)
    return out


def _has_supported_ts_filters(filters: List[dict]) -> bool:
    return any(bql_ts_index.is_supported_ts_filter(f) for f in (filters or []))


def execute(query_text, memory_root="memory/balloon_memory.balloondb", max_results=50, use_ts_index=True):
    ast = parse(query_text)
    filters = ast.get("filters", [])
    records = load_memory(memory_root)
    expanded = _expand_balloon(records, ast)
    limit = ast.get("top") or max_results or 50
    limit = max(1, min(int(limit), int(max_results or limit), 50))

    indexed_selected = False
    index_reason = "timestamp index disabled or no supported timestamp filter"
    filtered = None

    if use_ts_index and _has_supported_ts_filters(filters):
        try:
            index = bql_ts_index.build_index_from_records(expanded)
            refs = bql_ts_index.refs_for_filters(index, filters)
            candidate_positions = sorted(pos for pos in refs if isinstance(pos, int) and 0 <= pos < len(expanded))
            candidates = [expanded[pos] for pos in candidate_positions]
            filtered = _apply_filters(candidates, filters)
            indexed_selected = True
            index_reason = "in-memory timestamp index range lookup selected"
        except Exception as exc:
            filtered = None
            indexed_selected = False
            index_reason = "timestamp index fallback to full scan: " + str(exc)

    if filtered is None:
        filtered = _apply_filters(expanded, filters)

    plan = explain(ast, ts_index_available=indexed_selected)
    plan["ts_index_used"] = indexed_selected
    if indexed_selected:
        plan["ts_index_reason"] = index_reason
    elif plan.get("ts_index_candidate"):
        plan["ts_index_reason"] = index_reason

    results = _project(filtered, ast.get("return", []), limit)
    return {
        "status": "PASS_V03G8_BQL_QUERY_EXECUTED",
        "version": "V03G8_TS_INDEX_FOR_TIME_FILTER",
        "ast": ast,
        "plan": plan,
        "balloon_expand": {
            "expanded_count": len(expanded),
            "matched_count": len(filtered),
            "returned_count": len(results),
            "results": results
        },
        "safety": {
            "read_only": True,
            "no_write": True,
            "no_wal": True,
            "no_vector_engine": True,
            "no_network": True,
            "no_full_graph_export": True
        },
        "ts": int(time.time() * 1000)
    }
