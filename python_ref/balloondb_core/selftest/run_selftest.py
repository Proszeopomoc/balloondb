import json, html, time
from pathlib import Path
from balloondb_core.bql_parser import parse, ParseError
from balloondb_core.bql_planner import explain

ROOT = Path(__file__).resolve().parents[3]
CORE = ROOT / "python_ref" / "balloondb_core"

def run_selftest():
    data_dir = CORE / "data"
    report_dir = CORE / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    samples_path = data_dir / "sample_queries.txt"
    outputs_path = data_dir / "sample_outputs.jsonl"
    errors_path = data_dir / "errors.jsonl"
    report_path = report_dir / "validation_report.html"

    queries = [
        'FROM seed("PY_NAMEERROR_UNDEFINED_NAME") BALLOON radius=2 direction=up_down RETURN concept,evidence',
        'FROM concept("CONTROL_FLOW_STRUCTURE") BALLOON radius=2 direction=down RETURN evidence,signature',
        'EXPLAIN FROM seed("RUST_BRANCH_OR_LOOP_CONTRACT_FAIL") BALLOON radius=3 direction=up_down FILTER promotion_status="promoted_concept" RETURN route,evidence',
        'DELETE FROM seed("BAD") BALLOON radius=2 direction=up_down RETURN concept',
        'FROM seed("BAD_RADIUS") BALLOON radius=99 direction=up_down RETURN concept'
    ]
    samples_path.write_text("\n".join(queries) + "\n", encoding="utf-8")

    pass_count = 0
    fail_count = 0
    rows = []

    with outputs_path.open("w", encoding="utf-8") as out, errors_path.open("w", encoding="utf-8") as err:
        for q in queries:
            try:
                ast = parse(q)
                plan = explain(ast)
                rec = {"ok": True, "query": q, "ast": ast, "plan": plan}
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                pass_count += 1
                rows.append((q, "PASS", ""))
            except Exception as e:
                rec = {"ok": False, "query": q, "error": str(e)}
                err.write(json.dumps(rec, ensure_ascii=False) + "\n")
                if "DELETE" in q or "BAD_RADIUS" in q:
                    pass_count += 1
                    rows.append((q, "PASS_EXPECTED_REJECT", str(e)))
                else:
                    fail_count += 1
                    rows.append((q, "FAIL", str(e)))

    status = "PASS_V03G0_BQL_SELFTEST" if fail_count == 0 else "FAIL_V03G0_BQL_SELFTEST"

    html_rows = "\n".join(
        f"<tr><td>{html.escape(q)}</td><td>{html.escape(s)}</td><td>{html.escape(msg)}</td></tr>"
        for q, s, msg in rows
    )
    report = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>BalloonDB V03G0 BQL Selftest</title></head>
<body>
<h1>{html.escape(status)}</h1>
<p>pass_count={pass_count} fail_count={fail_count}</p>
<table border="1" cellpadding="6">
<tr><th>Query</th><th>Status</th><th>Message</th></tr>
{html_rows}
</table>
</body></html>
"""
    report_path.write_text(report, encoding="utf-8")

    return {
        "status": status,
        "version": "V03G0_BQL_READONLY_PARSER_AND_EXPLAIN",
        "pass_count": pass_count,
        "fail_count": fail_count,
        "samples": str(samples_path),
        "outputs": str(outputs_path),
        "errors": str(errors_path),
        "report": str(report_path),
        "ts": int(time.time() * 1000)
    }

if __name__ == "__main__":
    print(json.dumps(run_selftest(), ensure_ascii=False, indent=2))
