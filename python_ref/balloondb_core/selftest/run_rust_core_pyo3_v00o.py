from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from balloondb_core import binary_format_v00j as pyv00j
from balloondb_core.rust_core_v00o import (
    encode_record,
    decode_record,
    record_id_hex,
    rust_crc32,
    rust_available,
    write_bseed_v00j,
    read_bseed_v00j,
    v00j_record_id,
    v00j_write_file_bytes,
    canonical_payload,
)


def run_selftest() -> dict:
    repo = Path(__file__).resolve().parents[3]
    audit = repo / "audit" / "v00o"
    audit.mkdir(parents=True, exist_ok=True)

    # Legacy/lab BRS1 still works, but is not the default DB format.
    payload = b"hello-balloon-rust-core"
    logical_id = "seed:rust:v00o"
    kind = 1
    trust = 3
    encoded = encode_record(kind, trust, logical_id, payload)
    decoded = decode_record(encoded)
    expected_id = record_id_hex(kind, trust, logical_id, payload)
    legacy_checks = {
        "encoded_is_bytes": isinstance(encoded, (bytes, bytearray)),
        "decoded_kind": decoded["kind"] == kind,
        "decoded_trust": decoded["trust"] == trust,
        "decoded_logical_id": decoded["logical_id"] == logical_id,
        "decoded_payload": decoded["payload"] == payload,
        "record_id_match": decoded["record_id_hex"] == expected_id,
        "crc32_int": isinstance(rust_crc32(payload), int),
    }
    bad = bytearray(encoded)
    bad[-1] ^= 0x55
    try:
        decode_record(bytes(bad))
        legacy_checks["corrupt_detected"] = False
    except Exception:
        legacy_checks["corrupt_detected"] = True

    # Strict V00J byte boundary with deterministic created_ms.
    rows = [
        {"id": "PY_NAMEERROR", "trust": "VERIFIED", "n": 1, "x": 1.0, "y": 1.5},
        {"txt": "błąd", "ż": "ąćźń", "nested": {"b": 2, "a": [3, 1, 2]}, "ok": True, "nil": None},
    ]
    created_ms = 1781560000000
    rust_path = audit / "rust_strict_v00j.bseed"
    write_bseed_v00j(rust_path, rows, prefer_rust=True, created_ms=created_ms)
    header, read_back = read_bseed_v00j(rust_path, prefer_rust=True)
    payloads = [canonical_payload(r) for r in rows]
    rust_bytes = rust_path.read_bytes()
    ref_bytes = v00j_write_file_bytes(pyv00j.KIND_SEED, created_ms, payloads, prefer_rust=False)
    strict_checks = {
        "rust_extension_available": rust_available(),
        "rust_bytes_equal_reference": rust_bytes == ref_bytes,
        "read_payloads_match": [r.payload for r in read_back] == rows,
        "header_kind": int(header["kind"]) == pyv00j.KIND_SEED,
        "record_id_matches_python": v00j_record_id(payloads[0]) == pyv00j.record_id_from_payload(payloads[0]),
    }

    # Run the independent golden-vector acceptance gate.
    env = dict(**__import__("os").environ)
    env["BALLOONDB_REQUIRE_RUST_V00J"] = "1"
    proc = subprocess.run([sys.executable, "-m", "balloondb_core.selftest.run_v00j_rust_compat_v00o3"], cwd=repo, env=env, text=True, capture_output=True)
    strict_checks["golden_gate_exit_zero"] = proc.returncode == 0
    strict_checks["golden_gate_pass_seen"] = "PASS_V00O3_RUST_DROPIN_V00J_FORMAT_COMPAT" in proc.stdout
    (audit / "v00o3a_golden_gate_stdout.log").write_text(proc.stdout, encoding="utf-8")
    (audit / "v00o3a_golden_gate_stderr.log").write_text(proc.stderr, encoding="utf-8")

    status = "PASS_BALLOONDB_RUST_CORE_PYO3_V00O3A" if all(legacy_checks.values()) and all(strict_checks.values()) else "NO_GO_BALLOONDB_RUST_CORE_PYO3_V00O3A"
    report = {"status": status, "legacy_checks": legacy_checks, "strict_v00j_checks": strict_checks}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if status != "PASS_BALLOONDB_RUST_CORE_PYO3_V00O3A":
        raise SystemExit(1)
    print("PASS_BALLOONDB_RUST_CORE_PYO3_V00O3A")
    return report


if __name__ == "__main__":
    run_selftest()
