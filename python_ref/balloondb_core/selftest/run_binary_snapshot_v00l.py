from __future__ import annotations

import json
from pathlib import Path

from balloondb_core.binary_format_v00j import BalloonBinaryChecksumError, write_bbridge, write_bseed, write_bwal
from balloondb_core.binary_index_v00k import binary_mini_query, read_index
from balloondb_core.binary_snapshot_v00l import compact_wal_to_snapshot, corrupt_snapshot_seed, recover_snapshot


def resolve_repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parents[3], Path.cwd()]:
        if (candidate / "python_ref" / "balloondb_core").exists():
            return candidate
    return here.parents[3]


def main() -> int:
    repo = resolve_repo_root()
    py_root = repo / "python_ref"
    data = py_root / "balloondb_core" / "data" / "v00l_binary_snapshot_selftest"
    audit = repo / "audit" / "v00l"
    data.mkdir(parents=True, exist_ok=True)
    audit.mkdir(parents=True, exist_ok=True)

    base_bseed = data / "base.bseed"
    base_bbridge = data / "base.bbridge"
    wal = data / "delta.bwal"
    snapshot_root = data / "snapshots"

    base_seeds = [
        {"seed_id": "s:old", "type": "CONCEPT", "text": "old transient", "trust_state": "RAW", "source": "V00L_BASE"},
        {"seed_id": "s:alpha", "type": "CONCEPT", "text": "alpha", "trust_state": "VERIFIED", "source": "V00L_BASE"},
    ]
    base_bridges = [
        {"bridge_id": "br:old-alpha", "from": "s:old", "to": "s:alpha", "relation": "LINKS_TO", "trust_state": "RAW"},
    ]
    wal_entries = [
        {"op": "UPSERT_SEED", "payload": {"seed_id": "s:beta", "type": "CONCEPT", "text": "beta", "trust_state": "CANDIDATE", "source": "V00L_WAL"}},
        {"op": "UPSERT_SEED", "payload": {"seed_id": "s:alpha", "type": "CONCEPT", "text": "alpha promoted", "trust_state": "PROMOTED", "source": "V00L_WAL"}},
        {"op": "DELETE_SEED", "logical_id": "s:old"},
        {"op": "DELETE_BRIDGE", "logical_id": "br:old-alpha"},
        {"op": "UPSERT_BRIDGE", "payload": {"bridge_id": "br:alpha-beta", "from": "s:alpha", "to": "s:beta", "relation": "LINKS_TO", "trust_state": "VERIFIED"}},
        {"op": "UPSERT_BRIDGE", "payload": {"bridge_id": "br:beta-alpha", "from": "s:beta", "to": "s:alpha", "relation": "SUPPORTS", "trust_state": "CANDIDATE"}},
    ]

    write_bseed(base_bseed, base_seeds)
    write_bbridge(base_bbridge, base_bridges)
    write_bwal(wal, wal_entries)

    compact_meta = compact_wal_to_snapshot(base_bseed, base_bbridge, wal, snapshot_root, "snapshot_main")
    recovery = recover_snapshot(compact_meta["snapshot_dir"])

    _idx_header, idx_payload = read_index(Path(compact_meta["snapshot_dir"]) / "snapshot.bindex")
    q_promoted = binary_mini_query(idx_payload, "FIND trust_state=PROMOTED")
    q_concept = binary_mini_query(idx_payload, "FIND type=CONCEPT")
    q_relation = binary_mini_query(idx_payload, "FIND relation=LINKS_TO")
    q_deleted = binary_mini_query(idx_payload, "FIND logical_id=s:old")

    corrupt_detected = False
    corrupt_error = None
    corrupt_dir = corrupt_snapshot_seed(compact_meta["snapshot_dir"], data / "snapshot_corrupt")
    try:
        recover_snapshot(corrupt_dir)
    except BalloonBinaryChecksumError as e:
        corrupt_detected = True
        corrupt_error = str(e)

    checks = {
        "compact_pass": compact_meta["status"] == "PASS_BINARY_SNAPSHOT_COMPACTED_V00L",
        "recovery_pass": recovery["status"] == "PASS_BINARY_SNAPSHOT_RECOVERY_V00L",
        "seed_count_compacted": recovery["seed_count"] == 2,
        "bridge_count_compacted": recovery["bridge_count"] == 2,
        "index_record_count": recovery["index_record_count"] == 4,
        "wal_entry_count": compact_meta["wal_stats"]["wal_entry_count"] == 6,
        "old_seed_deleted": q_deleted["ok"] and q_deleted["count"] == 0,
        "promoted_lookup": q_promoted["ok"] and q_promoted["count"] == 1,
        "concept_lookup": q_concept["ok"] and q_concept["count"] == 2,
        "relation_lookup": q_relation["ok"] and q_relation["count"] == 1,
        "corrupt_snapshot_detected": corrupt_detected,
    }
    status = "PASS_BALLOONDB_BINARY_COMPACTION_SNAPSHOT_V00L" if all(checks.values()) else "NO_GO_BALLOONDB_BINARY_COMPACTION_SNAPSHOT_V00L"

    report = {
        "status": status,
        "version": "V00L_BINARY_COMPACTION_AND_SNAPSHOT",
        "repo_root": str(repo),
        "py_root": str(py_root),
        "data_root": str(data),
        "audit_root": str(audit),
        "compact_meta": compact_meta,
        "recovery": recovery,
        "checks": checks,
        "queries": {
            "trust_state_PROMOTED": q_promoted,
            "type_CONCEPT": q_concept,
            "relation_LINKS_TO": q_relation,
            "deleted_old_seed": q_deleted,
        },
        "corrupt_error": corrupt_error,
    }
    report_path = audit / "V00L_BINARY_COMPACTION_SNAPSHOT_REPORT.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(status)
    return 0 if status.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
