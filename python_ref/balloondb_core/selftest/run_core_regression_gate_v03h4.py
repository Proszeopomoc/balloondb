
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(r"C:\BalloonOperator")
OUT = ROOT / "06_EVIDENCE" / "BALLOONDB_V03H4_CORE_REGRESSION_RELEASE_GATE"

TEST_PLAN = [
    {
        "id": "V03H1_STORAGE",
        "kind": "ps1",
        "path": "09_SCRIPTS/RUN_STORAGE_SELFTEST_V03H1.ps1",
        "required": True,
        "group": "BalloonDB persistence core"
    },
    {
        "id": "V03H2_WAL",
        "kind": "ps1",
        "path": "09_SCRIPTS/RUN_WAL_SELFTEST_V03H2.ps1",
        "required": True,
        "group": "BalloonDB persistence core"
    },
    {
        "id": "V03H3_CRASH_RECOVERY",
        "kind": "ps1",
        "path": "09_SCRIPTS/RUN_CRASH_RECOVERY_SELFTEST_V03H3.ps1",
        "required": True,
        "group": "BalloonDB persistence core"
    },
    {
        "id": "V03G0_BQL_CORE",
        "kind": "ps1",
        "path": "09_SCRIPTS/RUN_BQL_SELFTEST_V03G0.ps1",
        "required": True,
        "group": "BQL core"
    },
    {
        "id": "V03G1_BQL_QUERY",
        "kind": "ps1",
        "path": "09_SCRIPTS/RUN_BQL_SELFTEST_V03G1.ps1",
        "required": True,
        "group": "BQL core"
    },
    {
        "id": "V03G2_BQL_FILTER_RANK",
        "kind": "ps1",
        "path": "09_SCRIPTS/RUN_BQL_SELFTEST_V03G2.ps1",
        "required": True,
        "group": "BQL core"
    },
    {
        "id": "V03G3_BQL_ERROR_CONTRACT",
        "kind": "ps1",
        "path": "09_SCRIPTS/RUN_BQL_SELFTEST_V03G3.ps1",
        "required": True,
        "group": "BQL core"
    },
    {
        "id": "V03G4_BQL_DAEMON",
        "kind": "ps1",
        "path": "09_SCRIPTS/RUN_BQL_SELFTEST_V03G4.ps1",
        "required": True,
        "group": "BQL daemon"
    },
    {
        "id": "V03G6_BQL_TIME_FILTER",
        "kind": "ps1",
        "path": "09_SCRIPTS/RUN_BQL_SELFTEST_V03G6.ps1",
        "required": True,
        "group": "BQL core"
    },
    {
        "id": "V03G7_BQL_FULL_REGRESSION",
        "kind": "ps1",
        "path": "09_SCRIPTS/RUN_BQL_REGRESSION_V03G7.ps1",
        "required": True,
        "group": "BQL regression"
    },
    {
        "id": "V03G8_TS_INDEX",
        "kind": "py",
        "path": "balloondb_core/selftest/run_selftest_v03g8.py",
        "required": False,
        "group": "BQL indexes"
    },
    {
        "id": "V03G9_QUERY_HISTORY_EXPLAIN",
        "kind": "py",
        "path": "balloondb_core/selftest/run_selftest_v03g9.py",
        "required": False,
        "group": "BQL reports"
    },
]

def now_ms():
    return int(time.time() * 1000)

def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)

def run_test(test):
    p = ROOT / test["path"]
    if not p.exists():
        status = "NO_GO_REQUIRED_TEST_MISSING" if test.get("required") else "SKIP_OPTIONAL_TEST_MISSING"
        return {
            "id": test["id"],
            "group": test["group"],
            "path": test["path"],
            "required": test["required"],
            "status": status,
            "returncode": None,
            "stdout_tail": "",
            "stderr_tail": "",
            "duration_ms": 0,
        }

    start = time.time()
    if test["kind"] == "ps1":
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(p)]
    else:
        cmd = ["py", str(p)]

    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    duration = int((time.time() - start) * 1000)
    ok = proc.returncode == 0
    return {
        "id": test["id"],
        "group": test["group"],
        "path": test["path"],
        "required": test["required"],
        "status": "PASS_TEST" if ok else "NO_GO_TEST_FAILED",
        "returncode": proc.returncode,
        "stdout_tail": (proc.stdout or "")[-5000:],
        "stderr_tail": (proc.stderr or "")[-5000:],
        "duration_ms": duration,
    }

def main():
    OUT.mkdir(parents=True, exist_ok=True)

    results = []
    for test in TEST_PLAN:
        results.append(run_test(test))

    required = [r for r in results if r["required"]]
    optional = [r for r in results if not r["required"]]
    required_pass = all(r["status"] == "PASS_TEST" for r in required)
    optional_ok = all(r["status"] in ("PASS_TEST", "SKIP_OPTIONAL_TEST_MISSING") for r in optional)

    status = "PASS_BALLOONDB_V03H4_CORE_REGRESSION_RELEASE_GATE" if required_pass and optional_ok else "NO_GO_BALLOONDB_V03H4_CORE_REGRESSION_RELEASE_GATE"

    groups = {}
    for r in results:
        groups.setdefault(r["group"], []).append({
            "id": r["id"],
            "status": r["status"],
            "required": r["required"],
            "duration_ms": r["duration_ms"]
        })

    report = {
        "status": status,
        "version": "BALLOONDB_V03H4_CORE_REGRESSION_RELEASE_GATE",
        "root": str(ROOT),
        "summary": {
            "required_total": len(required),
            "required_pass": sum(1 for r in required if r["status"] == "PASS_TEST"),
            "required_fail_or_missing": sum(1 for r in required if r["status"] != "PASS_TEST"),
            "optional_total": len(optional),
            "optional_pass": sum(1 for r in optional if r["status"] == "PASS_TEST"),
            "optional_skipped": sum(1 for r in optional if r["status"] == "SKIP_OPTIONAL_TEST_MISSING"),
        },
        "groups": groups,
        "results": results,
        "architecture_state": {
            "storage_v03h1": "required_pass" if any(r["id"] == "V03H1_STORAGE" and r["status"] == "PASS_TEST" for r in results) else "not_passed",
            "wal_v03h2": "required_pass" if any(r["id"] == "V03H2_WAL" and r["status"] == "PASS_TEST" for r in results) else "not_passed",
            "crash_recovery_v03h3": "required_pass" if any(r["id"] == "V03H3_CRASH_RECOVERY" and r["status"] == "PASS_TEST" for r in results) else "not_passed",
            "bql_regression": "required_pass" if any(r["id"] == "V03G7_BQL_FULL_REGRESSION" and r["status"] == "PASS_TEST" for r in results) else "not_passed",
            "operator_autonomy": "frozen_not_required_for_database_core",
            "api_usage": "none",
            "model_usage": "none",
        },
        "next_gate_if_pass": "BALLOONDB_V03H5_SIMPLE_CLI_AND_OPERATOR_MINIMAL_LOOP_PREP",
        "ts": now_ms(),
    }
    report["report"] = write_json(OUT / f"V03H4_CORE_REGRESSION_RELEASE_GATE_REPORT_{now_ms()}.json", report)

    compact = {
        "status": status,
        "summary": report["summary"],
        "architecture_state": report["architecture_state"],
        "report": report["report"],
    }
    print(json.dumps(compact, ensure_ascii=False, indent=2))
    return 0 if status.startswith("PASS") else 3

if __name__ == "__main__":
    raise SystemExit(main())
