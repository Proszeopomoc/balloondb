from __future__ import annotations

import json
import statistics
import time
from typing import Any

from balloondb_core import rust_batch_backend_v00q as q

BATCH_SIZES = [1, 100, 1000, 10000]

def make_rows(n: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i in range(n):
        rows.append({
            "id": i,
            "name": f"zażółć-{i % 17}",
            "kind": "seed" if i % 2 == 0 else "bridge",
            "score": 1.0,
            "nested": {"b": i % 5, "a": [i, i + 1, "ą"]},
        })
    return rows

def median_time(fn, repeats: int = 5) -> float:
    samples = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - t0)
    return statistics.median(samples)

def run() -> dict[str, Any]:
    if not q.rust_available():
        raise RuntimeError("RUST_BATCH_BACKEND_NOT_AVAILABLE")

    results = []
    all_equal = True

    for n in BATCH_SIZES:
        rows = make_rows(n)

        canonical_s = median_time(lambda: [q.canonical_payload(r) for r in rows])
        payloads = [q.canonical_payload(r) for r in rows]
        records = [(1 if i % 2 == 0 else 2, 1, p) for i, p in enumerate(payloads)]

        py_s = median_time(lambda: q.encode_batch_python(records))
        rust_s = median_time(lambda: q.encode_batch_rust(records))
        crossing_s = median_time(lambda: q.count_payload_bytes_rust(records))

        py_bytes = q.encode_batch_python(records)
        rust_bytes = q.encode_batch_rust(records)
        auto_backend, auto_bytes = q.encode_batch(records, backend="auto")
        fallback_backend, fallback_bytes = q.encode_batch(records, backend="python")

        bytes_equal = py_bytes == rust_bytes == auto_bytes == fallback_bytes
        all_equal = all_equal and bytes_equal

        py_us = (py_s / n) * 1_000_000
        rust_us = (rust_s / n) * 1_000_000
        canonical_us = (canonical_s / n) * 1_000_000
        crossing_us = (crossing_s / n) * 1_000_000

        results.append({
            "n": n,
            "payload_len_first": len(payloads[0]),
            "record_len_first": len(py_bytes[0]),
            "auto_backend": auto_backend,
            "fallback_backend": fallback_backend,
            "bytes_equal": bytes_equal,
            "canonical_json_us_per_record": canonical_us,
            "python_framing_us_per_record": py_us,
            "rust_batch_framing_us_per_record": rust_us,
            "pyo3_batch_crossing_count_us_per_record": crossing_us,
            "speedup_python_over_rust_batch": (py_us / rust_us) if rust_us else None,
            "rust_framing_minus_crossing_est_us_per_record": max(0.0, rust_us - crossing_us),
        })

    report = {
        "status": "PASS_BALLOONDB_RUST_BATCH_BACKEND_BENCHMARK_V00Q",
        "checks": {
            "rust_available": q.rust_available(),
            "all_batch_bytes_equal": all_equal,
            "batch_sizes": BATCH_SIZES,
            "speed_reported_not_pass_fail": True,
        },
        "results": results,
    }

    if not all_equal:
        report["status"] = "NO_GO_BALLOONDB_RUST_BATCH_BACKEND_BENCHMARK_V00Q"
        raise RuntimeError(json.dumps(report, ensure_ascii=False, indent=2))

    return report

if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
    print("PASS_BALLOONDB_RUST_BATCH_BACKEND_BENCHMARK_V00Q")
