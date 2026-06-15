from __future__ import annotations

import json
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
    write_records_v00j,
    read_records_v00j,
    v00j_record_id_u64,
)


def _payloads():
    return [
        {"logical_id": "seed:alpha", "role": "concept", "trust_state": "verified", "value": "zaĹĽĂłĹ‚Ä‡"},
        {"logical_id": "seed:beta", "role": "rule", "trust_state": "candidate", "value": [1, 2, 3]},
    ]


def run_selftest():
    repo = Path(__file__).resolve().parents[3]
    audit = repo / "audit" / "v00o"
    audit.mkdir(parents=True, exist_ok=True)

    payload = b"hello-balloon-rust-core"
    logical_id = "seed:rust:v00o"
    kind = 1
    trust = 3

    # V00O BRS1 lab compatibility remains alive.
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
    corrupt_detected = False
    corrupt_error = None
    bad = bytearray(encoded)
    bad[-1] ^= 0x55
    try:
        decode_record(bytes(bad))
    except Exception as exc:
        corrupt_detected = True
        corrupt_error = str(exc)
    legacy_checks["corrupt_detected"] = corrupt_detected

    # V00O3: real drop-in V00J format compatibility.
    rows = _payloads()
    python_written = audit / "python_written_v00j.bseed"
    rust_written = audit / "rust_written_v00j.bseed"
    python_fallback = audit / "python_fallback_v00j.bseed"
    corrupt_rust_written = audit / "rust_written_v00j_corrupt.bseed"

    pyv00j.write_bseed(python_written, rows)
    rust_header, rust_read_records = read_records_v00j(python_written, expected_kind=pyv00j.KIND_SEED, prefer_rust=True)

    write_bseed_v00j(rust_written, rows, prefer_rust=True)
    py_header, py_read_records = pyv00j.read_bseed(rust_written)

    write_bseed_v00j(python_fallback, rows, prefer_rust=False)
    fallback_header, fallback_records = read_bseed_v00j(python_fallback, prefer_rust=False)

    first_payload = pyv00j.canonical_payload(rows[0])
    expected_record_id = pyv00j.record_id_from_payload(first_payload)

    corrupt_data = bytearray(rust_written.read_bytes())
    corrupt_data[-1] ^= 0x33
    corrupt_rust_written.write_bytes(bytes(corrupt_data))
    v00j_corrupt_detected = False
    v00j_corrupt_error = None
    try:
        read_records_v00j(corrupt_rust_written, expected_kind=pyv00j.KIND_SEED, prefer_rust=True)
    except Exception as exc:
        v00j_corrupt_detected = True
        v00j_corrupt_error = str(exc)

    v00j_checks = {
        "rust_extension_available": rust_available(),
        "python_written_rust_read_count": len(rust_read_records) == len(rows),
        "python_written_rust_read_payloads": [r.payload for r in rust_read_records] == rows,
        "python_written_rust_header_kind": int(rust_header["kind"]) == pyv00j.KIND_SEED,
        "rust_written_python_read_count": len(py_read_records) == len(rows),
        "rust_written_python_read_payloads": [r.payload for r in py_read_records] == rows,
        "rust_written_python_header_kind": int(py_header["kind"]) == pyv00j.KIND_SEED,
        "record_id_same_as_python": v00j_record_id_u64(first_payload) == expected_record_id,
        "fallback_python_path_works": [r.payload for r in fallback_records] == rows and int(fallback_header["kind"]) == pyv00j.KIND_SEED,
        "v00j_corrupt_detected": v00j_corrupt_detected,
        "root_pyproject_exists": (repo / "pyproject.toml").exists(),
    }

    status = "PASS_BALLOONDB_RUST_DROPIN_V00J_COMPAT_V00O3" if all(legacy_checks.values()) and all(v00j_checks.values()) else "NO_GO_BALLOONDB_RUST_DROPIN_V00J_COMPAT_V00O3"
    report = {
        "status": status,
        "legacy_v00o_status": "PASS_BALLOONDB_RUST_CORE_PYO3_V00O" if all(legacy_checks.values()) else "NO_GO_BALLOONDB_RUST_CORE_PYO3_V00O",
        "checks_legacy_brs1": legacy_checks,
        "checks_v00j_dropin": v00j_checks,
        "encoded_len": len(encoded),
        "record_id_hex": expected_id,
        "corrupt_error": corrupt_error,
        "v00j_corrupt_error": v00j_corrupt_error,
        "python_written": str(python_written),
        "rust_written": str(rust_written),
    }
    (audit / "RUST_DROPIN_V00J_COMPAT_V00O3_REPORT.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if status.startswith("PASS_"):
        print("PASS_BALLOONDB_RUST_CORE_PYO3_V00O")
        print("PASS_BALLOONDB_RUST_DROPIN_V00J_COMPAT_V00O3")
        return report
    raise SystemExit(1)


if __name__ == "__main__":
    run_selftest()