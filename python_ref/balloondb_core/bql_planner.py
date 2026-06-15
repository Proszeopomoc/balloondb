def _supported_ts_filter(filter_obj: dict) -> bool:
    if not isinstance(filter_obj, dict):
        return False
    if filter_obj.get("field") != "ts":
        return False
    op = filter_obj.get("op")
    if op in {">", "<"}:
        return True
    return op == "in_window" and filter_obj.get("window") == "last_hour"


def _ts_index_reason(candidate: bool, available: bool) -> str:
    if candidate and available:
        return "supported timestamp filter and timestamp index available"
    if candidate and not available:
        return "supported timestamp filter present but timestamp index unavailable"
    return "no supported timestamp index filter"


def explain(ast: dict, ts_index_available: bool = False) -> dict:
    if not ast.get("read_only"):
        raise ValueError("only read-only AST is supported")

    src = ast["source"]
    balloon = ast["balloon"]
    filters = ast.get("filters", [])
    returns = ast.get("return", [])
    has_time_filter = any(f.get("field") == "ts" for f in filters if isinstance(f, dict))
    ts_index_candidate = any(_supported_ts_filter(f) for f in filters if isinstance(f, dict))
    ts_index_used = bool(ts_index_candidate and ts_index_available)
    ts_index_reason = _ts_index_reason(ts_index_candidate, ts_index_available)

    steps = [
        {
            "stage": "seed_lookup",
            "read_only": True,
            "source_kind": src["kind"],
            "source_value": src["value"],
            "bounded": True
        },
        {
            "stage": "balloon_expand",
            "read_only": True,
            "direction": balloon["direction"],
            "radius": balloon["radius"],
            "max_radius": 3,
            "no_full_graph_export": True
        }
    ]

    if ts_index_used:
        steps.append({
            "stage": "ts_index_range_lookup",
            "read_only": True,
            "field": "ts",
            "candidate_only": True,
            "persisted_index": False,
            "uses_wal": False
        })

    if filters:
        filter_step = {
            "stage": "filter",
            "read_only": True,
            "predicates": filters,
            "applied_inside_balloon": True
        }
        if has_time_filter:
            filter_step["time_filter"] = True
            filter_step["predicate_kind"] = "time"
        if ts_index_used:
            filter_step["candidate_source"] = "ts_index_range_lookup"
        steps.append(filter_step)

    steps.append({
        "stage": "return",
        "read_only": True,
        "fields": returns,
        "bounded_result": True,
        "returns_full_graph": False
    })

    return {
        "type": "BQL_EXPLAIN_PLAN",
        "version": "V03G8_TS_INDEX_FOR_TIME_FILTER",
        "feature_version": "V03G8_TS_INDEX_FOR_TIME_FILTER",
        "read_only": True,
        "ts_index_candidate": ts_index_candidate,
        "ts_index_used": ts_index_used,
        "ts_index_reason": ts_index_reason,
        "safety": {
            "no_write": True,
            "no_wal": True,
            "no_vector_engine": True,
            "no_network": True,
            "no_full_graph_export": True
        },
        "steps": steps
    }
