from __future__ import annotations

import json
from pathlib import Path

from balloondb_core.binary_format_v00j import write_bbridge, write_bseed
from balloondb_core.binary_index_v00k import (
    BalloonBinaryIndexChecksumError,
    binary_mini_query,
    build_index_from_files,
    corrupt_index_copy,
    lookup_record_id,
    lookup_trust_state,
    lookup_type,
    read_index,
    verify_index,
)


def resolve_repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parents[3], Path.cwd()]:
        if (candidate / "python_ref" / "balloondb_core").exists():
            return candidate
    return here.parents[3]


def main() -> int:
    repo = resolve_repo_root()
    py_root = repo / "python_ref"
    data = py_root / "balloondb_core" / "data" / "v00k_binary_index_selftest"
    audit = repo / "audit" / "v00k"
    data.mkdir(parents=True, exist_ok=True)
    audit.mkdir(parents=True, exist_ok=True)

    seeds = [
        {"seed_id": "s:alpha", "type": "CONCEPT", "text": "alpha", "trust_state": "VERIFIED", "source": "V00K_SELFTEST"},
        {"seed_id": "s:beta", "type": "CONCEPT", "text": "beta", "trust_state": "CANDIDATE", "source": "V00K_SELFTEST"},
        {"seed_id": "s:rule", "type": "RULE", "text": "alpha links to beta", "trust_state": "VERIFIED", "source": "V00K_SELFTEST"},
    ]
    bridges = [
        {"bridge_id": "br:alpha-beta", "from": "s:alpha", "to": "s:beta", "relation": "LINKS_TO", "trust_state": "VERIFIED"},
        {"bridge_id": "br:rule-alpha", "from": "s:rule", "to": "s:alpha", "relation": "SUPPORTS", "trust_state": "CANDIDATE"},
    ]

    bseed = data / "selftest.bseed"
    bbridge = data / "selftest.bbridge"
    bindex = data / "selftest.bindex"
    corrupt = data / "selftest_corrupt.bindex"

    write_bseed(bseed, seeds)
    write_bbridge(bbridge, bridges)
    index_meta = build_index_from_files(bindex, bseed, bbridge)
    header, index_payload = read_index(bindex)
    verify_meta = verify_index(bindex)

    first_record_id = index_payload["records"][0]["record_id"]
    q_record = binary_mini_query(index_payload, f"FIND record_id={first_record_id}")
    q_type = binary_mini_query(index_payload, "FIND type=CONCEPT")
    q_trust = binary_mini_query(index_payload, "FIND trust_state=VERIFIED")
    q_relation = binary_mini_query(index_payload, "FIND relation=LINKS_TO")
    q_bad = binary_mini_query(index_payload, "SELECT * FROM index")

    direct_record_lookup = lookup_record_id(index_payload, first_record_id)
    direct_type_lookup = lookup_type(index_payload, "CONCEPT")
    direct_trust_lookup = lookup_trust_state(index_payload, "VERIFIED")

    corrupt_detected = False
    corrupt_error = None
    corrupt_index_copy(bindex, corrupt)
    try:
        read_index(corrupt)
    except BalloonBinaryIndexChecksumError as e:
        corrupt_detected = True
        corrupt_error = str(e)

    checks = {
        "index_written": bindex.exists(),
        "index_record_count": index_payload.get("record_count") == 5,
        "verify_index": verify_meta["status"] == "PASS_BINARY_INDEX_VERIFY",
        "lookup_record_id": len(direct_record_lookup) == 1,
        "lookup_type_concept": len(direct_type_lookup) == 2,
        "lookup_trust_verified": len(direct_trust_lookup) == 3,
        "mini_query_record_id": q_record["ok"] and q_record["count"] == 1,
        "mini_query_type": q_type["ok"] and q_type["count"] == 2,
        "mini_query_trust_state": q_trust["ok"] and q_trust["count"] == 3,
        "mini_query_relation": q_relation["ok"] and q_relation["count"] == 1,
        "unsupported_query_rejected": (not q_bad["ok"]) and q_bad["status"] == "BINARY_QUERY_UNSUPPORTED_SYNTAX",
        "corrupt_index_detected": corrupt_detected,
    }
    status = "PASS_BALLOONDB_BINARY_INDEX_QUERY_V00K" if all(checks.values()) else "NO_GO_BALLOONDB_BINARY_INDEX_QUERY_V00K"

    report = {
        "status": status,
        "version": "V00K_BINARY_INDEX_AND_QUERY",
        "repo_root": str(repo),
        "py_root": str(py_root),
        "data_root": str(data),
        "audit_root": str(audit),
        "index_meta": index_meta,
        "verify_meta": verify_meta,
        "header": header,
        "checks": checks,
        "queries": {
            "record_id": q_record,
            "type": q_type,
            "trust_state": q_trust,
            "relation": q_relation,
            "unsupported": q_bad,
        },
        "corrupt_error": corrupt_error,
    }

    report_path = audit / "V00K_BINARY_INDEX_QUERY_REPORT.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(status)
    return 0 if status.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
