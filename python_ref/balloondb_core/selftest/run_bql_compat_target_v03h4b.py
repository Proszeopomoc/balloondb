from __future__ import annotations

import json
import os
import py_compile
import time
from pathlib import Path


def resolve_py_root():
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2],
        here.parents[3] / "python_ref",
        Path.cwd() / "python_ref",
        Path.cwd(),
    ]
    for c in candidates:
        if (c / "balloondb_core" / "bql_error_contract.py").exists():
            return c
    return here.parents[2]
from balloondb_core.bql_contract_runner import run_query_contract
from balloondb_core.bql_error_contract import write_json, write_jsonl, write_html_report
from balloondb_core.selftest.run_selftest_v03g1 import run_selftest as run_g1
from balloondb_core.selftest.run_selftest_v03g2 import run_selftest as run_g2

PY_ROOT = resolve_py_root().resolve()
REPO_ROOT = PY_ROOT.parent if PY_ROOT.name.lower() == "python_ref" else PY_ROOT
py_root = PY_ROOT
repo_root = REPO_ROOT
CORE = PY_ROOT / "balloondb_core"
DATA = CORE / "data" / "v03h4b_selftest"
REPORTS = CORE / "reports"
AUDIT = REPO_ROOT / "audit" / "v03h4b"


def now_ms() -> int:
    return int(time.time() * 1000)


def _write_synthetic_memory() -> Path:
    DATA.mkdir(parents=True, exist_ok=True)
    ts = now_ms()
    rows = [
        {
            "id": "REC_G0_DEPTH0",
            "seed_id": "PASS_V03G0_BQL_SELFTEST",
            "route": "synthetic_local_route",
            "evidence": "v03h4b_synthetic_memory",
            "concept": "bql_core",
            "pack": "code_patterns.bpack",
            "depth": 0,
            "pattern_id": "PATTERN_G0_0",
            "summary": "BQL core seed depth 0",
            "ts": ts,
        },
        {
            "id": "REC_G0_DEPTH1",
            "seed_id": "PASS_V03G0_BQL_SELFTEST",
            "route": "synthetic_local_route_depth_1",
            "evidence": "v03h4b_synthetic_memory",
            "concept": "bql_core",
            "pack": "code_patterns.bpack",
            "depth": 1,
            "pattern_id": "PATTERN_G0_1",
            "summary": "BQL core seed depth 1",
            "ts": ts,
        },
        {
            "id": "REC_G1",
            "seed_id": "PASS_V03G1_BQL_QUERY_EXECUTED",
            "route": "synthetic_query_route",
            "evidence": "v03h4b_synthetic_memory",
            "concept": "query_execution",
            "pack": "code_patterns.bpack",
            "depth": 1,
            "pattern_id": "PATTERN_G1",
            "summary": "BQL query executed over synthetic memory",
            "ts": ts,
        },
        {
            "id": "REC_G2",
            "seed_id": "PASS_V03G2_BQL_SELFTEST",
            "route": "synthetic_filter_route",
            "evidence": "v03h4b_synthetic_memory",
            "concept": "filter_rank_return",
            "pack": "code_patterns.bpack",
            "depth": 1,
            "pattern_id": "PATTERN_G2",
            "summary": "BQL filter/rank/return executed over synthetic memory",
            "ts": ts,
        },
    ]
    p = DATA / "synthetic_memory.jsonl"
    with p.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return p


def _compile_targets() -> list[dict]:
    rels = [
        "bql_error_contract.py",
        "bql_contract_runner.py",
        "bql_parser.py",
        "bql_executor.py",
        "selftest/run_selftest_v03g1.py",
        "selftest/run_selftest_v03g2.py",
        "selftest/run_selftest_v03g3.py",
        "selftest/run_bql_compat_target_v03h4b.py",
    ]
    out = []
    for rel in rels:
        path = CORE / rel
        try:
            py_compile.compile(str(path), doraise=True)
            out.append({"path": rel, "status": "PASS_COMPILE"})
        except Exception as exc:
            out.append({"path": rel, "status": "NO_GO_COMPILE", "error": str(exc)})
    return out


def _case(name: str, query: str, memory_root: Path, expect_ok=None, expect_status=None) -> dict:
    env = run_query_contract(query, memory_root=str(memory_root), max_results=50)
    ok = True
    if expect_ok is not None:
        ok = ok and (env.get("ok") == expect_ok)
    if expect_status is not None:
        ok = ok and (env.get("status") == expect_status)
    return {
        "name": name,
        "query": query,
        "expect": {"ok": expect_ok, "status": expect_status},
        "pass": bool(ok),
        "envelope": env,
    }


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    memory = _write_synthetic_memory()

    compile_results = _compile_targets()

    g1 = run_g1(str(memory))
    g2 = run_g2(str(memory))

    cases = [
        _case(
            "legal_EXECUTED_word_not_blocked",
            'FROM seed("PASS_V03G1_BQL_QUERY_EXECUTED") BALLOON radius=2 direction=up_down FILTER pack="code_patterns.bpack" RETURN pattern_id,summary TOP 5',
            memory,
            expect_ok=True,
            expect_status="PASS_V03G2_BQL_QUERY_EXECUTED",
        ),
        _case(
            "standalone_EXEC_rejected",
            'FROM seed("PASS_V03G1_BQL_QUERY_EXECUTED") BALLOON radius=2 direction=up_down FILTER pack="code_patterns.bpack" RETURN pattern_id EXEC TOP 5',
            memory,
            expect_ok=False,
            expect_status="BQL_UNSAFE_TOKEN",
        ),
        _case(
            "radius_gt_3_rejected_by_contract",
            'FROM seed("PASS_V03G1_BQL_QUERY_EXECUTED") BALLOON radius=4 direction=up_down RETURN pattern_id TOP 5',
            memory,
            expect_ok=False,
            expect_status="BQL_RADIUS_OUT_OF_BOUNDS",
        ),
        _case(
            "top_gt_50_rejected",
            'FROM seed("PASS_V03G1_BQL_QUERY_EXECUTED") BALLOON radius=2 direction=up_down RETURN pattern_id TOP 51',
            memory,
            expect_ok=False,
            expect_status="BQL_TOP_OUT_OF_BOUNDS",
        ),
        _case(
            "select_syntax_rejected_safely",
            'SELECT pattern_id FROM balloons WHERE pack="code_patterns.bpack" TOP 5',
            memory,
            expect_ok=False,
            expect_status="BQL_UNSUPPORTED_SYNTAX",
        ),
        _case(
            "query_output_contract_positive",
            'FROM seed("PASS_V03G2_BQL_SELFTEST") BALLOON radius=2 direction=up_down RETURN pattern_id,summary TOP 10',
            memory,
            expect_ok=True,
            expect_status="PASS_V03G2_BQL_QUERY_EXECUTED",
        ),
    ]

    checks = {
        "compile_all_targets": all(x["status"] == "PASS_COMPILE" for x in compile_results),
        "v03g1_compat_selftest": g1.get("status") == "PASS_V03G1_BQL_SELFTEST",
        "v03g2_compat_selftest": g2.get("status") == "PASS_V03G2_BQL_SELFTEST",
        "contract_cases_all_pass": all(c["pass"] for c in cases),
        "h4a_active_bug_removed": ((not (CORE / "selftest" / "bql_compat_fix_v03h4a.py").exists()) or ("HELPER = r" not in (CORE / "selftest" / "bql_compat_fix_v03h4a.py").read_text(encoding="utf-8", errors="replace"))),
        "synthetic_memory_local_only": str(memory).startswith(str(CORE)),
    }

    status = "PASS_V03H4B_TARGET_STATE_BQL_COMPAT" if all(checks.values()) else "NO_GO_V03H4B_TARGET_STATE_BQL_COMPAT"
    result = {
        "status": status,
        "version": "BALLOONDB_REPO_CLEANUP_V00C_AND_V03H4B_TARGET_STATE_BQL_COMPAT",
        "py_root": str(PY_ROOT),
        "repo_root": str(REPO_ROOT),
        "synthetic_memory": str(memory),
        "compile_results": compile_results,
        "g1": g1,
        "g2": g2,
        "checks": checks,
        "cases": [
            {
                "name": c["name"],
                "pass": c["pass"],
                "status": c["envelope"].get("status"),
                "ok": c["envelope"].get("ok"),
                "error_code": (c["envelope"].get("error") or {}).get("code"),
            }
            for c in cases
        ],
        "safety": {
            "read_only_external_sources": True,
            "no_network": True,
            "no_api_call": True,
            "no_operator_runtime_launch": True,
            "h4a_frozen": True,
        },
        "ts": now_ms(),
    }
    report_json = AUDIT / "V03H4B_TARGET_STATE_BQL_COMPAT_REPORT.json"
    report_html = AUDIT / "V03H4B_TARGET_STATE_BQL_COMPAT_REPORT.html"
    write_json(report_json, result)
    write_jsonl(AUDIT / "V03H4B_CASE_ENVELOPES.jsonl", [c["envelope"] for c in cases])
    write_html_report(report_html, "BalloonDB V03H4B target-state BQL compatibility", cases)
    result["report_json"] = str(report_json)
    result["report_html"] = str(report_html)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if status.startswith("PASS") else 9


if __name__ == "__main__":
    raise SystemExit(main())




