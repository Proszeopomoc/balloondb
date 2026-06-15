from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
import time
import datetime
import pathlib
import html

Path = pathlib.Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SCRIPTS_DIR = ROOT / "09_SCRIPTS"
DEFAULT_OUT_JSON = ROOT / "data" / "v03g7_bql_regression_report.json"
DEFAULT_OUT_HTML = ROOT / "reports" / "v03g7_bql_regression_summary.html"

REQUIRED_LAYERS = ["V03G0", "V03G1", "V03G2", "V03G3", "V03G4", "V03G6"]

CANONICAL_SCRIPTS = {
    "V03G0": "RUN_BQL_SELFTEST_V03G0.ps1",
    "V03G1": "RUN_BQL_SELFTEST_V03G1.ps1",
    "V03G2": "RUN_BQL_SELFTEST_V03G2.ps1",
    "V03G3": "RUN_BQL_SELFTEST_V03G3.ps1",
    "V03G4": "RUN_BQL_SELFTEST_V03G4.ps1",
    "V03G6": "RUN_BQL_SELFTEST_V03G6.ps1",
}

VERSION = "V03G7_REGRESSION_SUITE_ALL_BQL_LAYERS"
DEFAULT_TIMEOUT_SEC = 1800


def utc_now_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def now_ms():
    return int(time.time() * 1000)


def _decode_partial(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def resolve_under_root(value, label):
    raw = Path(value)
    if not raw.is_absolute():
        raw = ROOT / raw
    root_resolved = ROOT.resolve()
    target_resolved = raw.resolve()
    try:
        target_resolved.relative_to(root_resolved)
    except ValueError:
        raise ValueError(f"{label} must resolve under {ROOT}: {value}")
    return target_resolved


def parse_layers(text):
    if text is None or str(text).strip() == "":
        return list(REQUIRED_LAYERS)
    layers = []
    for part in str(text).split(","):
        layer = part.strip().upper()
        if not layer:
            continue
        if layer not in REQUIRED_LAYERS:
            raise ValueError(f"unknown layer requested: {layer}; allowed: {', '.join(REQUIRED_LAYERS)}")
        if layer not in layers:
            layers.append(layer)
    if not layers:
        raise ValueError("--layers did not contain any usable layer names")
    return layers


def discover_scripts(scripts_dir, requested_layers):
    discovered = []
    skipped = []
    for layer in REQUIRED_LAYERS:
        if layer not in requested_layers:
            skipped.append({"layer": layer, "reason": "not_requested", "script": str(scripts_dir / CANONICAL_SCRIPTS[layer])})
            continue
        script_path = scripts_dir / CANONICAL_SCRIPTS[layer]
        guarded_script = resolve_under_root(script_path, f"script for {layer}")
        if guarded_script.exists() and guarded_script.is_file():
            discovered.append({"layer": layer, "script": guarded_script})
        else:
            skipped.append({"layer": layer, "reason": "canonical_script_not_found", "script": str(guarded_script)})
    return discovered, skipped


def run_layer(layer, script_path, timeout_sec, verbose):
    started = time.time()
    started_utc = utc_now_iso()
    command = [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
    ]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "python_ref")
    env["PYTHONIOENCODING"] = "utf-8"

    if verbose:
        print(json.dumps({"event": "starting_layer", "layer": layer, "script": str(script_path)}, ensure_ascii=False), flush=True)

    try:
        proc = subprocess.run(
            command,
            cwd=str(ROOT),
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout_sec,
            encoding="utf-8",
            errors="replace",
        )
        ended = time.time()
        status = "PASS" if proc.returncode == 0 else "FAIL"
        return {
            "layer": layer,
            "script": str(script_path),
            "command": command,
            "status": status,
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "started_utc": started_utc,
            "ended_utc": utc_now_iso(),
            "duration_sec": round(ended - started, 3),
        }
    except subprocess.TimeoutExpired as exc:
        ended = time.time()
        return {
            "layer": layer,
            "script": str(script_path),
            "command": command,
            "status": "TIMEOUT",
            "exit_code": 124,
            "stdout": _decode_partial(exc.stdout),
            "stderr": _decode_partial(exc.stderr),
            "started_utc": started_utc,
            "ended_utc": utc_now_iso(),
            "duration_sec": round(ended - started, 3),
        }


def build_report(status, scripts_dir, discovered, skipped, results, timeout_sec):
    pass_count = sum(1 for row in results if row.get("status") == "PASS")
    fail_count = sum(1 for row in results if row.get("status") == "FAIL")
    timeout_count = sum(1 for row in results if row.get("status") == "TIMEOUT")
    return {
        "status": status,
        "version": VERSION,
        "root": str(ROOT),
        "scripts_dir": str(scripts_dir),
        "required_layers": list(REQUIRED_LAYERS),
        "discovered_layers": [row["layer"] for row in discovered],
        "skipped_layers": skipped,
        "summary": {
            "required_count": len(REQUIRED_LAYERS),
            "discovered_count": len(discovered),
            "skipped_count": len(skipped),
            "pass_count": pass_count,
            "fail_count": fail_count,
            "timeout_count": timeout_count,
            "timeout_sec_per_layer": int(timeout_sec),
        },
        "results": results,
        "safety": {
            "root_only": str(ROOT),
            "canonical_scripts_only": True,
            "recursive_globbing": False,
            "arbitrary_script_execution": False,
            "network_exposure": False,
            "subprocess_cwd": str(ROOT),
            "pythonpath_exact": str(ROOT / "python_ref"),
            "pythonioencoding": "utf-8",
        },
        "ts_ms": now_ms(),
    }


def write_json_report(path, report):
    guarded = resolve_under_root(path, "out-json")
    guarded.parent.mkdir(parents=True, exist_ok=True)
    guarded.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return guarded


def _excerpt(text, limit=4000):
    if text is None:
        return ""
    s = str(text)
    if len(s) <= limit:
        return s
    return s[:limit] + "\n... [truncated]"


def write_html_report(path, report):
    guarded = resolve_under_root(path, "out-html")
    guarded.parent.mkdir(parents=True, exist_ok=True)

    result_rows = []
    for row in report.get("results", []):
        result_rows.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('layer', '')))}</td>"
            f"<td>{html.escape(str(row.get('status', '')))}</td>"
            f"<td>{html.escape(str(row.get('exit_code', '')))}</td>"
            f"<td>{html.escape(str(row.get('duration_sec', '')))}</td>"
            f"<td>{html.escape(str(row.get('script', '')))}</td>"
            f"<td><pre>{html.escape(_excerpt(row.get('stdout', '')))}</pre></td>"
            f"<td><pre>{html.escape(_excerpt(row.get('stderr', '')))}</pre></td>"
            "</tr>"
        )

    skipped_rows = []
    for row in report.get("skipped_layers", []):
        skipped_rows.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('layer', '')))}</td>"
            f"<td>{html.escape(str(row.get('reason', '')))}</td>"
            f"<td>{html.escape(str(row.get('script', '')))}</td>"
            "</tr>"
        )

    summary = report.get("summary", {})
    doc = """<!doctype html>
<html><head><meta charset="utf-8"><title>BalloonDB V03G7 BQL Regression Suite</title></head>
<body>
<h1>{status}</h1>
<p>version={version}</p>
<p>root={root}</p>
<p>scripts_dir={scripts_dir}</p>
<p>discovered_count={discovered_count} skipped_count={skipped_count} pass_count={pass_count} fail_count={fail_count} timeout_count={timeout_count}</p>
<h2>Layer Results</h2>
<table border="1" cellpadding="6">
<tr><th>Layer</th><th>Status</th><th>Exit Code</th><th>Duration Sec</th><th>Script</th><th>Stdout Excerpt</th><th>Stderr Excerpt</th></tr>
{result_rows}
</table>
<h2>Skipped Layers</h2>
<table border="1" cellpadding="6">
<tr><th>Layer</th><th>Reason</th><th>Script</th></tr>
{skipped_rows}
</table>
</body></html>
""".format(
        status=html.escape(str(report.get("status", ""))),
        version=html.escape(str(report.get("version", ""))),
        root=html.escape(str(report.get("root", ""))),
        scripts_dir=html.escape(str(report.get("scripts_dir", ""))),
        discovered_count=html.escape(str(summary.get("discovered_count", 0))),
        skipped_count=html.escape(str(summary.get("skipped_count", 0))),
        pass_count=html.escape(str(summary.get("pass_count", 0))),
        fail_count=html.escape(str(summary.get("fail_count", 0))),
        timeout_count=html.escape(str(summary.get("timeout_count", 0))),
        result_rows="\n".join(result_rows),
        skipped_rows="\n".join(skipped_rows),
    )
    guarded.write_text(doc, encoding="utf-8")
    return guarded


def run_regression(args):
    scripts_dir = resolve_under_root(args.scripts_dir, "scripts-dir")
    out_json = resolve_under_root(args.out_json, "out-json")
    out_html = resolve_under_root(args.out_html, "out-html")
    if args.timeout < 1:
        raise ValueError("--timeout must be a positive number of seconds")

    requested_layers = parse_layers(args.layers)
    discovered, skipped = discover_scripts(scripts_dir, requested_layers)
    results = []

    if not discovered:
        status = "PASS_NO_AVAILABLE_LAYERS_ALLOWED" if args.allow_empty else "FAIL_NO_AVAILABLE_LAYERS"
        report = build_report(status, scripts_dir, discovered, skipped, results, args.timeout)
        json_path = write_json_report(out_json, report)
        html_path = write_html_report(out_html, report)
        compact = {
            "status": status,
            "version": VERSION,
            "discovered_layers": [],
            "skipped_count": len(skipped),
            "out_json": str(json_path),
            "out_html": str(html_path),
            "ts_ms": report["ts_ms"],
        }
        print(json.dumps(compact, ensure_ascii=False, separators=(",", ":")))
        return report

    for row in discovered:
        results.append(run_layer(row["layer"], row["script"], args.timeout, args.verbose))

    if results and all(row.get("status") == "PASS" for row in results):
        status = "PASS_V03G7_BQL_REGRESSION_SUITE"
    else:
        status = "FAIL_V03G7_BQL_REGRESSION_SUITE"

    report = build_report(status, scripts_dir, discovered, skipped, results, args.timeout)
    json_path = write_json_report(out_json, report)
    html_path = write_html_report(out_html, report)
    compact = {
        "status": status,
        "version": VERSION,
        "discovered_layers": report["discovered_layers"],
        "summary": report["summary"],
        "out_json": str(json_path),
        "out_html": str(html_path),
        "ts_ms": report["ts_ms"],
    }
    print(json.dumps(compact, ensure_ascii=False, separators=(",", ":")))
    return report


def build_arg_parser():
    parser = argparse.ArgumentParser(description="BalloonDB V03G7 all-layer BQL regression runner")
    parser.add_argument("--scripts-dir", default=str(DEFAULT_SCRIPTS_DIR))
    parser.add_argument("--out-json", default=str(DEFAULT_OUT_JSON))
    parser.add_argument("--out-html", default=str(DEFAULT_OUT_HTML))
    parser.add_argument("--layers", default=",".join(REQUIRED_LAYERS))
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SEC)
    parser.add_argument("--allow-empty", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv=None):
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        report = run_regression(args)
    except Exception as exc:
        failure = {
            "status": "FAIL_V03G7_BQL_REGRESSION_RUNNER_ERROR",
            "version": VERSION,
            "error": str(exc),
            "root": str(ROOT),
            "safety": {
                "root_only": str(ROOT),
                "network_exposure": False,
                "no_write_outside_root": True,
            },
            "ts_ms": now_ms(),
        }
        print(json.dumps(failure, ensure_ascii=False, separators=(",", ":")), file=sys.stderr)
        return 3
    return 0 if str(report.get("status", "")).startswith("PASS") else 3


if __name__ == "__main__":
    raise SystemExit(main())
