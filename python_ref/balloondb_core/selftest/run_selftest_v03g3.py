import json
import time
from pathlib import Path

from balloondb_core.bql_contract_runner import run_query_contract
from balloondb_core.bql_error_contract import write_jsonl, write_html_report, write_json

ROOT = Path(r"C:\BalloonOperator")
CORE = ROOT / "balloondb_core"
EVIDENCE = ROOT / "06_EVIDENCE" / "BALLOONDB_BQL_CORE"

def _case(name, query, memory_root, expect_ok=None, expect_status=None):
    env = run_query_contract(query, memory_root=memory_root, max_results=50)
    ok = True
    if expect_ok is not None:
        ok = ok and (env.get("ok") == expect_ok)
    if expect_status is not None:
        ok = ok and (env.get("status") == expect_status)
    return {
        "name": name,
        "query": query,
        "expect": f"ok={expect_ok} status={expect_status}",
        "pass": bool(ok),
        "envelope": env
    }

def run_selftest(memory_root):
    data_dir = CORE / "data"
    report_dir = CORE / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)

    cases = [
        _case(
            "legal_EXECUTED_word_not_blocked",
            'FROM seed("PASS_V03G1_BQL_QUERY_EXECUTED") BALLOON radius=2 direction=up_down FILTER pack="code_patterns.bpack" RETURN pattern_id,summary TOP 5',
            memory_root,
            expect_ok=True,
            expect_status="PASS_V03G2_BQL_QUERY_EXECUTED"
        ),
        _case(
            "standalone_EXEC_rejected",
            'FROM seed("PASS_V03G1_BQL_QUERY_EXECUTED") BALLOON radius=2 direction=up_down FILTER pack="code_patterns.bpack" RETURN pattern_id EXEC TOP 5',
            memory_root,
            expect_ok=False,
            expect_status="BQL_UNSAFE_TOKEN"
        ),
        _case(
            "radius_gt_3_rejected_by_executor",
            'FROM seed("PASS_V03G1_BQL_QUERY_EXECUTED") BALLOON radius=4 direction=up_down RETURN pattern_id TOP 5',
            memory_root,
            expect_ok=False,
            expect_status="BQL_RADIUS_OUT_OF_BOUNDS"
        ),
        _case(
            "top_gt_50_rejected",
            'FROM seed("PASS_V03G1_BQL_QUERY_EXECUTED") BALLOON radius=2 direction=up_down RETURN pattern_id TOP 51',
            memory_root,
            expect_ok=False,
            expect_status="BQL_TOP_OUT_OF_BOUNDS"
        ),
        _case(
            "select_syntax_rejected_safely",
            'SELECT pattern_id FROM balloons WHERE pack="code_patterns.bpack" TOP 5',
            memory_root,
            expect_ok=False,
            expect_status="BQL_UNSUPPORTED_SYNTAX"
        ),
        _case(
            "query_output_contract_positive",
            'FROM seed("PASS_V03G2_BQL_SELFTEST") BALLOON radius=2 direction=up_down RETURN pattern_id,summary TOP 10',
            memory_root,
            expect_ok=True,
            expect_status="PASS_V03G2_BQL_QUERY_EXECUTED"
        ),
    ]

    jsonl_path = data_dir / "v03g3_selftest_output.jsonl"
    html_path = report_dir / "v03g3_selftest_report.html"
    envelope_path = EVIDENCE / "V03G3_SELFTEST_ENVELOPE.json"

    write_jsonl(jsonl_path, [c["envelope"] for c in cases])
    write_html_report(html_path, "BalloonDB V03G3 query report and error contract", cases)

    pass_count = sum(1 for c in cases if c["pass"])
    fail_count = sum(1 for c in cases if not c["pass"])
    status = "PASS_V03G3_BQL_SELFTEST" if fail_count == 0 else "FAIL_V03G3_BQL_SELFTEST"

    result = {
        "status": status,
        "version": "V03G3_BQL_QUERY_REPORT_AND_ERROR_CONTRACT",
        "pass_count": pass_count,
        "fail_count": fail_count,
        "output": str(jsonl_path),
        "report": str(html_path),
        "envelope": str(envelope_path),
        "cases": [
            {
                "name": c["name"],
                "pass": c["pass"],
                "status": c["envelope"].get("status"),
                "error_code": (c["envelope"].get("error") or {}).get("code")
            }
            for c in cases
        ],
        "safety": {
            "read_only": True,
            "no_write": True,
            "no_wal": True,
            "no_vector_engine": True,
            "no_full_graph_export": True
        },
        "ts": int(time.time() * 1000)
    }
    write_json(envelope_path, result)
    return result
