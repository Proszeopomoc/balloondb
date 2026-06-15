import argparse, json, sys
from pathlib import Path
from .bql_parser import parse, ParseError
from .bql_planner import explain as make_plan
from .role_map_loader import load_role_map

def _read_query(args):
    if getattr(args, "query_file", None):
        with open(args.query_file, "r", encoding="utf-8-sig") as f:
            return f.read().strip()
    if getattr(args, "query", None):
        return args.query
    if getattr(args, "positional_query", None):
        return args.positional_query
    return ""

def cmd_parse(args):
    ast = parse(_read_query(args))
    print(json.dumps(ast, ensure_ascii=False, indent=2))
    return 0

def cmd_explain(args):
    ast = parse(_read_query(args))
    plan = make_plan(ast)
    print(json.dumps({"ast": ast, "plan": plan}, ensure_ascii=False, indent=2))
    return 0

def _write_jsonl(path, result):
    if not path:
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for row in result.get("balloon_expand", {}).get("results", []):
            f.write(json.dumps(row, ensure_ascii=False) + "\\n")

def _write_html(path, result):
    if not path:
        return
    import html
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for r in result.get("balloon_expand", {}).get("results", []):
        rows.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(str(r.get("rank"))),
                html.escape(str(r.get("pack"))),
                html.escape(str(r.get("depth"))),
                html.escape(str(r.get("record_id")))
            )
        )
    doc = """<!doctype html><html><head><meta charset="utf-8"><title>BalloonDB V03G2 Query Report</title></head>
<body><h1>{}</h1><p>returned_count={}</p><table border="1" cellpadding="6"><tr><th>Rank</th><th>Pack</th><th>Depth</th><th>Record</th></tr>{}</table></body></html>""".format(
        html.escape(result.get("status", "")),
        result.get("balloon_expand", {}).get("returned_count", 0),
        "\\n".join(rows)
    )
    p.write_text(doc, encoding="utf-8")

def cmd_query(args):
    from .bql_executor import execute
    result = execute(
        _read_query(args),
        memory_root=args.memory_root,
        max_results=args.max_results
    )
    _write_jsonl(getattr(args, "out_jsonl", None), result)
    _write_html(getattr(args, "out_html", None), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"].startswith("PASS") else 4

def cmd_validate_scripts(args):
    result = load_role_map(args.role_map)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 2

def cmd_selftest(args):
    from .selftest.run_selftest import run_selftest
    result = run_selftest()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "PASS_V03G0_BQL_SELFTEST" else 3

def cmd_selftest_v03g1(args):
    from .selftest.run_selftest_v03g1 import run_selftest
    result = run_selftest(args.memory_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "PASS_V03G1_BQL_SELFTEST" else 5

def cmd_selftest_v03g2(args):
    from .selftest.run_selftest_v03g2 import run_selftest
    result = run_selftest(args.memory_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "PASS_V03G2_BQL_SELFTEST" else 6

def _query_args(p):
    p.add_argument("--query", required=False, default="")
    p.add_argument("--query-file", required=False)

def _query_exec_args(p):
    p.add_argument("--memory-root", default=str(Path(__file__).resolve().parents[2] / "examples" / "core_small" / "memory" / "balloon_memory.balloondb"))
    p.add_argument("--max-results", type=int, default=50)
    p.add_argument("--out-jsonl", required=False, default="")
    p.add_argument("--out-html", required=False, default="")

def main(argv=None):
    ap = argparse.ArgumentParser(prog="balloondb-bql", description="BalloonDB BQL")
    ap.add_argument("positional_query", nargs="?", help="Optional direct BQL query")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("parse")
    _query_args(p)
    p.set_defaults(fn=cmd_parse)

    p = sub.add_parser("explain")
    _query_args(p)
    p.set_defaults(fn=cmd_explain)

    p = sub.add_parser("query")
    _query_args(p)
    _query_exec_args(p)
    p.set_defaults(fn=cmd_query)

    p = sub.add_parser("validate-scripts")
    p.add_argument("--role-map", default=str(Path(__file__).resolve().parents[2] / "examples" / "config" / "BALLOONDB_V03G0_SCRIPT_ROLE_MAP.json"))
    p.set_defaults(fn=cmd_validate_scripts)

    p = sub.add_parser("selftest")
    p.set_defaults(fn=cmd_selftest)

    p = sub.add_parser("selftest-v03g1")
    p.add_argument("--memory-root", default=str(Path(__file__).resolve().parents[2] / "examples" / "core_small" / "memory" / "balloon_memory.balloondb"))
    p.set_defaults(fn=cmd_selftest_v03g1)

    p = sub.add_parser("selftest-v03g2")
    p.add_argument("--memory-root", default=str(Path(__file__).resolve().parents[2] / "examples" / "core_small" / "memory" / "balloon_memory.balloondb"))
    p.set_defaults(fn=cmd_selftest_v03g2)

    args = ap.parse_args(argv)

    if args.cmd is None and args.positional_query:
        args.memory_root = str(Path(__file__).resolve().parents[2] / "examples" / "core_small" / "memory" / "balloon_memory.balloondb")
        args.max_results = 50
        args.out_jsonl = ""
        args.out_html = ""
        return cmd_query(args)

    if args.cmd is None:
        ap.print_help()
        return 0

    try:
        return args.fn(args)
    except ParseError as e:
        print(json.dumps({"status": "BQL_PARSE_ERROR", "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
