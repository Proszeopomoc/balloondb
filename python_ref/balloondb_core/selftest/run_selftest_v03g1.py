from __future__ import annotations

import html
import json
import os
import time
from pathlib import Path

from balloondb_core.bql_executor import execute

ROOT = Path(os.environ.get("BALLOONDB_ROOT", Path.cwd()))
CORE = ROOT / "balloondb_core"


def run_selftest(memory_root):
    data_dir = CORE / "data"
    report_dir = CORE / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    query = 'FROM seed("PASS_V03G0_BQL_SELFTEST") BALLOON radius=2 direction=up_down RETURN route,evidence,concept'
    result = execute(query, memory_root=memory_root, max_results=30)
    balloon = result.get("balloon_expand", {})
    out_path = data_dir / "v03g1_selftest_output.jsonl"
    out_path.write_text(json.dumps(result, ensure_ascii=False) + "\n", encoding="utf-8")

    ok = str(result.get("status", "")).startswith("PASS") and balloon.get("returned_count", 0) >= 1
    status = "PASS_V03G1_BQL_SELFTEST" if ok else "FAIL_V03G1_BQL_SELFTEST"

    report_path = report_dir / "v03g1_selftest_report.html"
    report_path.write_text(
        '<!doctype html><meta charset="utf-8"><h1>' + html.escape(status) + '</h1>'
        + '<p>expanded_count=' + str(balloon.get("expanded_count", 0)) + '</p>'
        + '<p>returned_count=' + str(balloon.get("returned_count", 0)) + '</p>'
        + '<pre>' + html.escape(json.dumps(result.get("safety", {}), ensure_ascii=False, indent=2)) + '</pre>',
        encoding="utf-8",
    )
    return {
        "status": status,
        "version": "V03G1_BQL_SEED_LOOKUP_AND_BALLOON_EXPAND_V0_COMPAT_H4B",
        "query": query,
        "expanded_count": balloon.get("expanded_count", 0),
        "returned_count": balloon.get("returned_count", 0),
        "output": str(out_path),
        "report": str(report_path),
        "ts": int(time.time() * 1000),
    }
