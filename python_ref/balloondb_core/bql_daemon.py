import argparse
import json
import socketserver
import threading
import time
from pathlib import Path

from . import bql_executor
from .bql_contract_runner import run_query_contract

_ORIGINAL_LOAD_MEMORY = bql_executor.load_memory
_CACHE = {}
_STATS = {
    "cache_hits": 0,
    "cache_misses": 0,
    "query_count": 0,
    "started_ms": int(time.time() * 1000),
}
_LOCK = threading.RLock()

def cached_load_memory(memory_root):
    key = str(Path(memory_root))
    with _LOCK:
        if key in _CACHE:
            _STATS["cache_hits"] += 1
            return _CACHE[key]
        _STATS["cache_misses"] += 1
        snap = _ORIGINAL_LOAD_MEMORY(memory_root)
        _CACHE[key] = snap
        return snap

# Patch executor global loader. execute() uses this module global.
bql_executor.load_memory = cached_load_memory

def daemon_stats():
    with _LOCK:
        return {
            "status": "PASS_V03G4_DAEMON_STATS",
            "version": "V03G4_BQL_HOT_DAEMON_AND_PACK_CACHE",
            "cache_keys": sorted(_CACHE.keys()),
            "cache_size": len(_CACHE),
            "cache_hits": _STATS["cache_hits"],
            "cache_misses": _STATS["cache_misses"],
            "query_count": _STATS["query_count"],
            "uptime_ms": int(time.time() * 1000) - _STATS["started_ms"],
            "read_only": True,
            "localhost_only": True,
        }

class BQLDaemonHandler(socketserver.StreamRequestHandler):
    def handle(self):
        peer = self.client_address[0]
        if peer not in ("127.0.0.1", "::1", "localhost"):
            self.wfile.write(json.dumps({
                "ok": False,
                "status": "BQL_DAEMON_REJECT_NON_LOCALHOST",
                "peer": peer
            }).encode("utf-8") + b"\n")
            return

        line = self.rfile.readline(10_000_000)
        try:
            req = json.loads(line.decode("utf-8-sig"))
            cmd = req.get("cmd", "query")

            if cmd == "stats":
                resp = daemon_stats()

            elif cmd == "shutdown":
                resp = {"status": "PASS_V03G4_DAEMON_SHUTDOWN_REQUESTED"}
                threading.Thread(target=self.server.shutdown, daemon=True).start()

            elif cmd == "query":
                query = req.get("query", "")
                memory_root = req.get("memory_root") or self.server.memory_root
                max_results = int(req.get("max_results", 50))

                with _LOCK:
                    _STATS["query_count"] += 1

                t0 = time.perf_counter()
                env = run_query_contract(query, memory_root=memory_root, max_results=max_results)
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                env["daemon"] = {
                    "version": "V03G4_BQL_HOT_DAEMON_AND_PACK_CACHE",
                    "elapsed_ms": round(elapsed_ms, 3),
                    "cache_keys": sorted(_CACHE.keys()),
                    "cache_hits": _STATS["cache_hits"],
                    "cache_misses": _STATS["cache_misses"],
                    "query_count": _STATS["query_count"],
                    "localhost_only": True,
                }
                resp = env

            else:
                resp = {"ok": False, "status": "BQL_DAEMON_UNKNOWN_COMMAND", "cmd": cmd}

        except Exception as exc:
            resp = {
                "ok": False,
                "status": "BQL_DAEMON_ERROR",
                "error": {
                    "type": exc.__class__.__name__,
                    "message": str(exc)
                }
            }

        self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8") + b"\n")

class LocalBQLDaemon(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

def run_server(host, port, memory_root):
    server = LocalBQLDaemon((host, port), BQLDaemonHandler)
    server.memory_root = memory_root
    print(json.dumps({
        "status": "PASS_V03G4_DAEMON_STARTED",
        "host": host,
        "port": port,
        "memory_root": memory_root,
        "read_only": True,
        "localhost_only": True
    }, ensure_ascii=False), flush=True)
    server.serve_forever()

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--memory-root", default=r"C:\BalloonOperator\memory\balloon_memory.balloondb")
    args = ap.parse_args(argv)

    if args.host not in ("127.0.0.1", "localhost", "::1"):
        raise SystemExit("V03G4 refuses non-localhost binding")

    run_server(args.host, args.port, args.memory_root)

if __name__ == "__main__":
    main()
