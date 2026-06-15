import json

def make_ast(explain, source_type, source_value, radius, direction, filters, returns, top=None):
    return {
        "type": "BQL_QUERY",
        "read_only": True,
        "explain": bool(explain),
        "source": {
            "kind": source_type,
            "value": source_value
        },
        "balloon": {
            "radius": int(radius),
            "direction": direction
        },
        "filters": filters or [],
        "return": returns or [],
        "top": int(top) if top is not None else None,
        "safety": {
            "bounded_radius": True,
            "no_write": True,
            "no_full_graph_export": True
        }
    }

def json_line(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)
