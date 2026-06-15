from __future__ import annotations

import html
import json
import traceback
from pathlib import Path
from typing import Any, Iterable

try:
    from .bql_time_filter import TimeFilterError
except Exception:  # pragma: no cover - import fallback for standalone diagnostics
    class TimeFilterError(Exception):
        pass

ERROR_CONTRACT_VERSION = "V03H4B_TARGET_STATE_BQL_COMPAT"
PASS_COMPAT_STATUS = "PASS_V03G2_BQL_QUERY_EXECUTED"


def _message(exc: BaseException) -> str:
    return str(exc or "")


def classify_error(exc: BaseException) -> dict[str, Any]:
    """Return stable BQL error metadata.

    This function is deliberately conservative: it maps legacy parser/executor
    messages into stable public status codes used by the BQL compatibility
    selftests. It does not promote any AI/model output to truth.
    """
    name = exc.__class__.__name__
    message = _message(exc)
    lower = message.lower()

    if isinstance(exc, TimeFilterError) or "time filter" in lower or "named window" in lower or "timestamp" in lower:
        status = "BQL_TIME_FILTER_PARSE_ERROR"
    elif "unsafe token rejected" in lower:
        status = "BQL_UNSAFE_TOKEN"
    elif "radius out of bounds" in lower:
        status = "BQL_RADIUS_OUT_OF_BOUNDS"
    elif "top out of bounds" in lower:
        status = "BQL_TOP_OUT_OF_BOUNDS"
    elif "select syntax not enabled" in lower or "unsupported bql syntax" in lower:
        status = "BQL_UNSUPPORTED_SYNTAX"
    elif "bql_seed_not_found" in lower or "seed_not_found" in lower:
        status = "BQL_SEED_NOT_FOUND"
    elif isinstance(exc, PermissionError):
        status = "BQL_READONLY_SAFETY_ERROR"
    elif name == "ParseError":
        status = "BQL_PARSE_ERROR"
    elif isinstance(exc, ValueError):
        status = "BQL_EXECUTION_ERROR"
    else:
        status = "BQL_INTERNAL_ERROR"

    return {
        "status": status,
        "code": status,
        "error_class": name,
        "message": message,
        "feature_version": ERROR_CONTRACT_VERSION,
        "retryable": False,
    }


def classify_bql_error(exc: BaseException) -> dict[str, Any]:
    return classify_error(exc)


def ok_envelope(query: str, result: dict[str, Any] | None) -> dict[str, Any]:
    result = result or {}
    engine_status = result.get("status", "PASS")
    return {
        "ok": True,
        "status": PASS_COMPAT_STATUS,
        "engine_status": engine_status,
        "feature_version": ERROR_CONTRACT_VERSION,
        "query": query,
        "result": result,
        "error": None,
    }


def error_envelope(query: str, exc: BaseException, include_trace: bool = False) -> dict[str, Any]:
    err = classify_error(exc)
    env = {
        "ok": False,
        "status": err["status"],
        "feature_version": ERROR_CONTRACT_VERSION,
        "query": query,
        "result": None,
        "error": {
            "code": err["code"],
            "class": err["error_class"],
            "message": err["message"],
            "retryable": err["retryable"],
        },
    }
    if include_trace:
        env["trace"] = traceback.format_exc()
    return env


def contract_error_response(exc: BaseException, query: str | None = None) -> dict[str, Any]:
    return error_envelope(query or "", exc)


def error_json_line(exc: BaseException, query: str | None = None) -> str:
    return json.dumps(contract_error_response(exc, query=query), ensure_ascii=False, sort_keys=True)


def write_json(path: str | Path, obj: Any) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(p)


def write_jsonl(path: str | Path, rows: Iterable[Any]) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return str(p)


def write_html_report(path: str | Path, title: str, cases: Iterable[dict[str, Any]]) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for case in cases:
        env = case.get("envelope", {}) or {}
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(case.get('name', '')))}</td>"
            f"<td>{html.escape('PASS' if case.get('pass') else 'FAIL')}</td>"
            f"<td>{html.escape(str(env.get('status', '')))}</td>"
            f"<td><pre>{html.escape(json.dumps(env.get('error'), ensure_ascii=False, indent=2))}</pre></td>"
            "</tr>"
        )
    doc = """<!doctype html>
<meta charset="utf-8">
<title>{title}</title>
<h1>{title}</h1>
<table border="1" cellpadding="6">
<tr><th>case</th><th>pass</th><th>status</th><th>error</th></tr>
{rows}
</table>
""".format(title=html.escape(title), rows="\n".join(rows))
    p.write_text(doc, encoding="utf-8")
    return str(p)
