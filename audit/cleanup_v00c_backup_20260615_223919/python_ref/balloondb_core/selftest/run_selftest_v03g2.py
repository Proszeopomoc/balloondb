import json, html, time
from pathlib import Path
from balloondb_core.bql_executor import execute

ROOT = Path(r"C:\BalloonOperator")
CORE = ROOT / "balloondb_core"

def run_selftest(memory_root):
    data_dir = CORE / "data"
    report_dir = CORE / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    queries = [
        'FROM seed("PASS_V03G1_BQL_QUERY_EXECUTED") BALLOON radius=2 direction=up_down FILTER pack="code_patterns.bpack" RETURN pattern_id,summary TOP 5',
        'FROM seed("PASS_V03G0_BQL_SELFTEST") BALLOON radius=2 direction=up_down FILTER depth=1 RETURN route,evidence,concept TOP 10'
    ]

    out_path = data_dir / "v03g2_selftest_output.jsonl"
    report_path = report_dir / "v03g2_selftest_report.html"

    results = []
    pass_count = 0
    fail_count = 0

    with out_path.open("w", encoding="utf-8") as f:
        for q in queries:
            res = execute(q, memory_root=memory_root, max_results=50)
            f.write(json.dumps(res, ensure_ascii=False) + "\\n")
            ok = res["status"].startswith("PASS") and res["balloon_expand"]["returned_count"] <= 50
            if ok:
                pass_count += 1
            else:
                fail_count += 1
            results.append((q, res, ok))

    status = "PASS_V03G2_BQL_SELFTEST" if fail_count == 0 else "FAIL_V03G2_BQL_SELFTEST"

    rows = []
    for q, res, ok in results:
        rows.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(q),
                "PASS" if ok else "FAIL",
                res["seed_lookup"]["match_count"],
                res["balloon_expand"]["returned_count"]
            )
        )

    doc = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>BalloonDB V03G2 Selftest</title></head>
<body>
<h1>{html.escape(status)}</h1>
<p>pass_count={pass_count} fail_count={fail_count}</p>
<table border="1" cellpadding="6">
<tr><th>Query</th><th>Status</th><th>Seed matches</th><th>Returned</th></tr>
{''.join(rows)}
</table>
</body></html>
"""
    report_path.write_text(doc, encoding="utf-8")

    return {
        "status": status,
        "version": "V03G2_BQL_FILTER_RANK_RETURN",
        "pass_count": pass_count,
        "fail_count": fail_count,
        "output": str(out_path),
        "report": str(report_path),
        "ts": int(time.time() * 1000)
    }
