from __future__ import annotations

import json
from pathlib import Path

from balloondb_core.binary_format_v00j import (
    KIND_BRIDGE,
    KIND_SEED,
    KIND_WAL,
    BalloonBinaryChecksumError,
    corrupt_copy,
    read_bbridge,
    read_bseed,
    replay_bwal,
    verify_records,
    write_bbridge,
    write_bseed,
    write_bwal,
    write_manifest,
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
    data = py_root / "balloondb_core" / "data" / "v00j_binary_selftest"
    audit = repo / "audit" / "v00j"
    data.mkdir(parents=True, exist_ok=True)
    audit.mkdir(parents=True, exist_ok=True)

    seeds = [
        {"seed_id": "s:balloondb", "text": "BalloonDB", "trust_state": "VERIFIED", "source": "V00J_SELFTEST"},
        {"seed_id": "s:bql", "text": "BQL", "trust_state": "VERIFIED", "source": "V00J_SELFTEST"},
        {"seed_id": "s:wal", "text": "WAL", "trust_state": "VERIFIED", "source": "V00J_SELFTEST"},
    ]
    bridges = [
        {"bridge_id": "b:1", "from": "s:balloondb", "to": "s:bql", "relation": "HAS_QUERY_LAYER", "trust_state": "VERIFIED"},
        {"bridge_id": "b:2", "from": "s:balloondb", "to": "s:wal", "relation": "HAS_DURABILITY_LAYER", "trust_state": "VERIFIED"},
    ]
    wal_entries = [
        {"op": "PUT_SEED", "payload": seeds[0]},
        {"op": "PUT_SEED", "payload": seeds[1]},
        {"op": "PUT_BRIDGE", "payload": bridges[0]},
        {"op": "CHECKPOINT", "payload": {"records": 3}},
    ]

    bseed = data / "selftest.bseed"
    bbridge = data / "selftest.bbridge"
    bwal = data / "selftest.bwal"
    manifest = data / "MANIFEST.bdbm"
    corrupt = data / "selftest_corrupt.bseed"

    seed_meta = write_bseed(bseed, seeds)
    bridge_meta = write_bbridge(bbridge, bridges)
    wal_meta = write_bwal(bwal, wal_entries)

    seed_header, seed_records = read_bseed(bseed)
    bridge_header, bridge_records = read_bbridge(bbridge)
    replayed = replay_bwal(bwal)

    verify_seed = verify_records(bseed, expected_kind=KIND_SEED)
    verify_bridge = verify_records(bbridge, expected_kind=KIND_BRIDGE)
    verify_wal = verify_records(bwal, expected_kind=KIND_WAL)

    corrupt_copy(bseed, corrupt)
    corrupt_detected = False
    corrupt_error = None
    try:
        read_bseed(corrupt)
    except BalloonBinaryChecksumError as e:
        corrupt_detected = True
        corrupt_error = str(e)

    manifest_meta = write_manifest(
        manifest,
        [seed_meta, bridge_meta, wal_meta],
        extra={"selftest": "V00J_BINARY_DB_CORE", "corrupt_detected": corrupt_detected},
    )

    checks = {
        "seed_write_read_count": len(seed_records) == len(seeds),
        "bridge_write_read_count": len(bridge_records) == len(bridges),
        "wal_replay_count": len(replayed) == len(wal_entries),
        "crc_corrupt_detected": corrupt_detected,
        "manifest_written": manifest.exists(),
        "verify_seed": verify_seed["status"] == "PASS_BINARY_VERIFY",
        "verify_bridge": verify_bridge["status"] == "PASS_BINARY_VERIFY",
        "verify_wal": verify_wal["status"] == "PASS_BINARY_VERIFY",
    }
    status = "PASS_BALLOONDB_BINARY_FORMAT_V00J" if all(checks.values()) else "NO_GO_BALLOONDB_BINARY_FORMAT_V00J"

    report = {
        "status": status,
        "version": "V00J_BINARY_DB_CORE",
        "repo_root": str(repo),
        "py_root": str(py_root),
        "data_root": str(data),
        "audit_root": str(audit),
        "files": {
            "bseed": seed_meta,
            "bbridge": bridge_meta,
            "bwal": wal_meta,
            "manifest": manifest_meta,
            "corrupt_copy": str(corrupt),
        },
        "headers": {"seed": seed_header, "bridge": bridge_header},
        "checks": checks,
        "corrupt_error": corrupt_error,
    }

    report_path = audit / "V00J_BINARY_DB_CORE_REPORT.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(status)
    return 0 if status.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
