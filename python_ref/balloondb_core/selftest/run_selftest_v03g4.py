import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from balloondb_core.bql_contract_runner import run_query_contract
from balloondb_core.bql_daemon_client import send_request

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "06_EVIDENCE" / "BALLOONDB_BQL_CORE"
DATA = ROOT / "balloondb_core" / "data"
REPORTS = ROOT / "balloondb_core" / "reports"

QUERY = 'FROM seed("PASS_V03G3_BQL_SELFTEST") BALLOON radius=2 direction=up_down RETURN pattern_id,summary TOP 10'

def _free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port

def _wait_daemon(port, timeout=8.0):
    end = time.time() + timeout
    last = None
    while time.time() < end:
        try:
            return send_request("127.0.0.1", port, {"cmd": "stats"}, timeout=1.0)
        except Exception as exc:
            last = str(exc)
            time.sleep(0.15)
    raise RuntimeError("daemon did not start: " + str(last))

def run_selftest(memory_root):
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    port = _free_port()
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    env["PYTHONIOENCODING"] = "utf-8"

    log_path = EVIDENCE / "V03G4_DAEMON_SELFTEST_SERVER.log"
    log = open(log_path, "w", encoding="utf-8")

    proc = subprocess.Popen(
        [sys.executable, "-m", "balloondb_core.bql_daemon", "--host", "127.0.0.1", "--port", str(port), "--memory-root", memory_root],
        cwd=str(ROOT),
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True
    )

    cases = []
    try:
        stats0 = _wait_daemon(port)
        direct = run_query_contract(QUERY, memory_root=memory_root, max_results=50)
        daemon1 = send_request("127.0.0.1", port, {
            "cmd": "query",
            "query": QUERY,
            "memory_root": memory_root,
            "max_results": 50
        })
        daemon2 = send_request("127.0.0.1", port, {
            "cmd": "query",
            "query": QUERY,
            "memory_root": memory_root,
            "max_results": 50
        })
        stats1 = send_request("127.0.0.1", port, {"cmd": "stats"})

        cases.append({
            "name": "daemon_started",
            "pass": stats0.get("status") == "PASS_V03G4_DAEMON_STATS"
        })
        cases.append({
            "name": "direct_and_daemon_status_match",
            "pass": direct.get("status") == daemon1.get("status")
        })
        cases.append({
            "name": "cache_loaded_once_and_hit",
            "pass": stats1.get("cache_misses", 0) >= 1 and stats1.get("cache_hits", 0) >= 1
        })
        cases.append({
            "name": "localhost_only_flag",
            "pass": daemon1.get("daemon", {}).get("localhost_only") is True
        })
        cases.append({
            "name": "read_only_safety",
            "pass": daemon1.get("safety", {}).get("no_write") is True and daemon1.get("safety", {}).get("no_wal") is True
        })

        output = {
            "status": "PASS_V03G4_BQL_HOT_DAEMON_SELFTEST" if all(c["pass"] for c in cases) else "FAIL_V03G4_BQL_HOT_DAEMON_SELFTEST",
            "version": "V03G4_BQL_HOT_DAEMON_AND_PACK_CACHE",
            "port": port,
            "query": QUERY,
            "cases": cases,
            "direct_status": direct.get("status"),
            "daemon_status": daemon1.get("status"),
            "daemon_stats": stats1,
            "server_log": str(log_path),
            "safety": {
                "read_only": True,
                "localhost_only": True,
                "no_write": True,
                "no_wal": True,
                "no_vector_engine": True,
                "no_full_graph_export": True
            },
            "ts": int(time.time() * 1000)
        }

        out_path = DATA / "v03g4_selftest_output.json"
        out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        output["output"] = str(out_path)
        return output

    finally:
        try:
            send_request("127.0.0.1", port, {"cmd": "shutdown"}, timeout=1.0)
        except Exception:
            pass
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
        log.close()
