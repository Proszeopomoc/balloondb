"""
run_v00j_rust_compat_v00o3.py  --  acceptance gate for V00O3_RUST_DROPIN_V00J_FORMAT_COMPAT

Defines "drop-in correct" for the Rust V00J backend. Runs now (validates the Python
reference + locked golden vectors) and, once the Rust PyO3 module exposes the V00J API,
cross-checks Rust <-> Python byte-for-byte.

Exit 0 = PASS or PENDING (rust not built yet). Exit 1 = NO_GO (a real mismatch).
"""
import json, struct, hashlib, zlib, binascii, sys, os

# ---- independent reference (verified byte-identical to binary_format_v00j) ----
MAGIC = {1: b"BSEEDJ00", 2: b"BBRDGJ00", 3: b"BWAL0J00"}
FH = struct.Struct("<8sHHIQQ32s")
RH = struct.Struct("<QIIII")

def canon(p): return json.dumps(p, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
def rec_id(pb): return int.from_bytes(hashlib.sha256(pb).digest()[:8], "little")
def crc(pb): return zlib.crc32(pb) & 0xFFFFFFFF

def ref_write_file(kind, created_ms, payload_bytes_list):
    out = FH.pack(MAGIC[kind], 1, kind, 64, created_ms, len(payload_bytes_list), b"\x00" * 32)
    for pb in payload_bytes_list:
        out += RH.pack(rec_id(pb), len(pb), crc(pb), 0, 0) + pb
    return out

# ---- locked golden vectors (the canonicalizer contract) ----
GOLDEN = [
    ({}, "7b7d", 9973137080230810436, 2745614147),
    ({"id": "PY_NAMEERROR", "trust": "VERIFIED", "n": 1, "x": 1.0, "y": 1.5},
     "7b226964223a2250595f4e414d454552524f52222c226e223a312c227472757374223a225645524946494544222c2278223a312e302c2279223a312e357d",
     1746617285619952443, 1188715145),
    ({"txt": "błąd", "ż": "ąćźń", "nested": {"b": 2, "a": [3, 1, 2]}, "ok": True, "nil": None},
     "7b226e6573746564223a7b2261223a5b332c312c325d2c2262223a327d2c226e696c223a6e756c6c2c226f6b223a747275652c22747874223a2262c582c48564222c22c5bc223a22c485c487c5bac584227d",
     16859162784457723423, 3856007266),
]

def main():
    checks = {}
    fail = []

    # 1) golden vectors lock the canonicalization + id + crc
    g_ok = True
    for payload, hex_expected, id_expected, crc_expected in GOLDEN:
        pb = canon(payload)
        if pb.hex() != hex_expected or rec_id(pb) != id_expected or crc(pb) != crc_expected:
            g_ok = False
            fail.append(f"golden mismatch for {payload!r}")
    checks["golden_vectors"] = g_ok

    # 2) reference == live Python module, byte-for-byte (if the module is importable)
    try:
        from balloondb_core.binary_format_v00j import write_records, read_records, KIND_SEED
        import tempfile, os
        payloads = [p for p, *_ in GOLDEN] + [{"a": 2 ** 53, "b": -5, "c": [0]}]
        d = tempfile.mkdtemp(); path = os.path.join(d, "t.bseed")
        write_records(path, KIND_SEED, payloads)
        real = open(path, "rb").read()
        created = struct.unpack("<8sHHIQQ32s", real[:64])[4]
        mine = ref_write_file(KIND_SEED, created, [canon(p) for p in payloads])
        checks["reference_matches_module"] = (real == mine)
        if real != mine:
            fail.append("reference bytes != binary_format_v00j bytes")
    except ImportError:
        checks["reference_matches_module"] = "SKIPPED_module_not_on_path"

    # 3) Rust V00J drop-in (the real V00O3 target)
    rust = None
    try:
        import balloondb_core_rs as _rs
        if all(hasattr(_rs, n) for n in ("v00j_record_id", "v00j_encode_record", "v00j_write_file", "v00j_read_file")):
            rust = _rs
    except Exception:
        rust = None

    if rust is None:
        require_rust = os.environ.get("BALLOONDB_REQUIRE_RUST_V00J", "0") == "1"
        status = "NO_GO_V00O3_RUST_V00J_NOT_IMPLEMENTED" if require_rust else ("PENDING_V00O3_RUST_V00J_NOT_IMPLEMENTED" if (g_ok and not fail) else "NO_GO_V00O3_REFERENCE_BROKEN")
        checks["rust_v00j_backend"] = "ABSENT"
        print(json.dumps({"status": status, "checks": checks, "fail": fail,
                          "note": "Reference + golden are the gate's Python half. Strict runner requires the Rust V00J API."}, ensure_ascii=False, indent=2))
        sys.exit(1 if require_rust or fail else 0)

    # Rust present -> full byte-for-byte cross-check
    created = 1781560000000
    payloads = [canon(p) for p, *_ in GOLDEN]
    ref_bytes = ref_write_file(1, created, payloads)
    rust_bytes = bytes(rust.v00j_write_file(1, created, payloads))
    checks["rust_write_bytes_identical"] = (rust_bytes == ref_bytes)
    if rust_bytes != ref_bytes:
        fail.append("rust v00j_write_file bytes != reference")

    parsed = rust.v00j_read_file(ref_bytes)
    recs = parsed["records"]
    checks["rust_read_ids_match"] = all(recs[i]["record_id"] == rec_id(payloads[i]) for i in range(len(payloads)))
    checks["rust_read_payloads_match"] = all(bytes(recs[i]["payload"]) == payloads[i] for i in range(len(payloads)))
    checks["rust_record_id_fn"] = all(rust.v00j_record_id(pb) == rec_id(pb) for pb in payloads)
    for k in ("rust_read_ids_match", "rust_read_payloads_match", "rust_record_id_fn"):
        if not checks[k]:
            fail.append(k)

    status = "PASS_V00O3_RUST_DROPIN_V00J_FORMAT_COMPAT" if not fail else "NO_GO_V00O3_RUST_V00J_MISMATCH"
    print(json.dumps({"status": status, "checks": checks, "fail": fail}, ensure_ascii=False, indent=2))
    sys.exit(0 if not fail else 1)

if __name__ == "__main__":
    main()
