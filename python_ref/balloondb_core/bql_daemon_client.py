import argparse
import json
import socket
import statistics
import time
from pathlib import Path

def send_request(host, port, req, timeout=10.0):
    data = json.dumps(req, ensure_ascii=False).encode("utf-8") + b"\n"
    with socket.create_connection((host, port), timeout=timeout) as s:
        s.sendall(data)
        chunks = []
        while True:
            b = s.recv(65536)
            if not b:
                break
            chunks.append(b)
            if b"\n" in b:
                break
    raw = b"".join(chunks).decode("utf-8-sig").strip()
    return json.loads(raw)

def read_query(query, query_file):
    if query_file:
        return Path(query_file).read_text(encoding="utf-8-sig").strip()
    return query or ""

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--cmd", default="query", choices=["query", "stats", "shutdown", "bench"])
    ap.add_argument("--query", default="")
    ap.add_argument("--query-file", default="")
    ap.add_argument("--memory-root", default=r"C:\BalloonOperator\memory\balloon_memory.balloondb")
    ap.add_argument("--max-results", type=int, default=50)
    ap.add_argument("--repeat", type=int, default=20)
    ap.add_argument("--out-json", default="")
    args = ap.parse_args(argv)

    if args.cmd == "bench":
        query = read_query(args.query, args.query_file)
        times = []
        last = None
        for _ in range(max(1, args.repeat)):
            t0 = time.perf_counter()
            last = send_request(args.host, args.port, {
                "cmd": "query",
                "query": query,
                "memory_root": args.memory_root,
                "max_results": args.max_results
            })
            times.append((time.perf_counter() - t0) * 1000.0)
        result = {
            "status": "PASS_V03G4_DAEMON_BENCHMARK",
            "repeat": len(times),
            "p50_ms": round(statistics.median(times), 3),
            "p95_ms": round(sorted(times)[max(0, int(len(times) * 0.95) - 1)], 3),
            "min_ms": round(min(times), 3),
            "max_ms": round(max(times), 3),
            "last_status": last.get("status") if isinstance(last, dict) else None,
            "last_daemon": last.get("daemon") if isinstance(last, dict) else None
        }
    else:
        req = {"cmd": args.cmd}
        if args.cmd == "query":
            req.update({
                "query": read_query(args.query, args.query_file),
                "memory_root": args.memory_root,
                "max_results": args.max_results
            })
        result = send_request(args.host, args.port, req)

    if args.out_json:
        p = Path(args.out_json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if str(result.get("status", "")).startswith("PASS") or result.get("ok") is True else 3

if __name__ == "__main__":
    raise SystemExit(main())
