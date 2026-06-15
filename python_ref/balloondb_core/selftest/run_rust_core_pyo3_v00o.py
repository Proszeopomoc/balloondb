import json
from pathlib import Path

from balloondb_core.rust_core_v00o import encode_record, decode_record, record_id_hex, rust_crc32


def run_selftest():
    payload = b"hello-balloon-rust-core"
    logical_id = "seed:rust:v00o"
    kind = 1
    trust = 3

    encoded = encode_record(kind, trust, logical_id, payload)
    decoded = decode_record(encoded)
    expected_id = record_id_hex(kind, trust, logical_id, payload)

    checks = {
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
    checks["corrupt_detected"] = corrupt_detected

    status = "PASS_BALLOONDB_RUST_CORE_PYO3_V00O" if all(checks.values()) else "NO_GO_BALLOONDB_RUST_CORE_PYO3_V00O"
    report = {
        "status": status,
        "checks": checks,
        "encoded_len": len(encoded),
        "record_id_hex": expected_id,
        "corrupt_error": corrupt_error,
    }

    repo = Path(__file__).resolve().parents[3]
    audit = repo / "audit" / "v00o"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "RUST_CORE_PYO3_V00O_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = run_selftest()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"].startswith("PASS") else 1)
