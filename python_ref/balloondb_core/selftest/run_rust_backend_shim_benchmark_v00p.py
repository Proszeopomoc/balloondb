#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import time

from balloondb_core import rust_backend_shim_v00p as shim


def _bench(fn, n: int = 3000) -> float:
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) * 1_000_000.0 / n


def main() -> int:
    row = {
        "z": "żółć",
        "a": 1.0,
        "nested": {"b": 2, "a": [3, 1.0, "ą"]},
        "plain": "BalloonDB",
    }
    payload = shim.canonical_payload(row)
    checks = {}
    checks["canonical_payload_is_bytes"] = isinstance(payload, bytes)
    checks["canonical_payload_sorted"] = payload.startswith(b'{"a":1.0,')
    checks["rust_available"] = shim.rust_available()
    checks["selected_backend_is_rust"] = shim.selected_backend() == "rust"

    py_id = shim.record_id_u64(row, backend="python")
    rust_id = shim.record_id_u64(row, backend="rust")
    checks["record_id_match"] = py_id == rust_id

    py_record = shim.encode_record(row, kind=7, trust=3, backend="python")
    rust_record = shim.encode_record(row, kind=7, trust=3, backend="rust")
    auto_record = shim.encode_record(row, kind=7, trust=3, backend="auto")
    checks["python_record_is_bytes"] = isinstance(py_record, bytes)
    checks["rust_record_is_bytes"] = isinstance(rust_record, bytes)
    checks["rust_python_bytes_equal"] = rust_record == py_record
    checks["auto_uses_same_bytes"] = auto_record == py_record

    old = os.environ.get("BALLOONDB_DISABLE_RUST")
    os.environ["BALLOONDB_DISABLE_RUST"] = "1"
    try:
        checks["fallback_backend_is_python"] = shim.selected_backend() == "python"
        checks["fallback_bytes_equal"] = shim.encode_record(row, kind=7, trust=3, backend="auto") == py_record
    finally:
        if old is None:
            os.environ.pop("BALLOONDB_DISABLE_RUST", None)
        else:
            os.environ["BALLOONDB_DISABLE_RUST"] = old

    py_us = _bench(lambda: shim.encode_record(row, kind=7, trust=3, backend="python"))
    rust_us = _bench(lambda: shim.encode_record(row, kind=7, trust=3, backend="rust"))
    report = {
        "status": "PASS_BALLOONDB_RUST_BACKEND_SHIM_BENCHMARK_V00P" if all(checks.values()) else "NO_GO_BALLOONDB_RUST_BACKEND_SHIM_BENCHMARK_V00P",
        "checks": checks,
        "payload_len": len(payload),
        "record_len": len(py_record),
        "python_encode_us": py_us,
        "rust_encode_us": rust_us,
        "speedup_python_over_rust": (py_us / rust_us) if rust_us > 0 else None,
        "note": "speed is reported, not used as a pass/fail condition",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"].startswith("PASS_"):
        print(report["status"])
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
