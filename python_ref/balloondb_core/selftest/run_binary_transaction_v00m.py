from __future__ import annotations

import json
import shutil
from pathlib import Path

from balloondb_core.binary_transaction_v00m import (
    commit_snapshot,
    stage_snapshot,
    recover_latest_complete_snapshot,
    corrupt_snapshot_seed_payload,
    NoCompleteSnapshotError,
)


def repo_root() -> Path:
    here = Path(__file__).resolve()
    # .../python_ref/balloondb_core/selftest/run_*.py -> repo root
    return here.parents[3]


def main() -> int:
    root = repo_root()
    audit = root / "audit" / "v00m" / "selftest"
    if audit.exists():
        shutil.rmtree(audit)
    audit.mkdir(parents=True, exist_ok=True)
    db = audit / "transaction_db"

    seeds_v1 = [
        {"record_id": "seed-alpha", "type": "concept", "trust_state": "RAW", "payload": "alpha"},
        {"record_id": "seed-beta", "type": "concept", "trust_state": "VERIFIED", "payload": "beta"},
    ]
    bridges_v1 = [
        {"record_id": "bridge-alpha-beta", "type": "bridge", "relation": "LINKS", "trust_state": "CANDIDATE", "from": "seed-alpha", "to": "seed-beta"},
    ]
    commit_snapshot(db, 1, seeds_v1, bridges_v1)
    recovered_v1 = recover_latest_complete_snapshot(db)

    # Stage incomplete version 2. Recovery must keep version 1.
    seeds_v2 = seeds_v1 + [{"record_id": "seed-gamma", "type": "concept", "trust_state": "PROMOTED", "payload": "gamma"}]
    stage_snapshot(db, 2, seeds_v2, bridges_v1, complete=False)
    recovered_after_incomplete = recover_latest_complete_snapshot(db)

    # Commit complete version 2. Recovery must move to version 2.
    commit_snapshot(db, 2, seeds_v2, bridges_v1)
    recovered_v2 = recover_latest_complete_snapshot(db)

    # Corrupt current version 2. Recovery must fallback to version 1.
    corrupt_path = corrupt_snapshot_seed_payload(db, 2)
    recovered_after_corrupt = recover_latest_complete_snapshot(db)

    checks = {
        "initial_commit_recovers_v1": recovered_v1["recovered_version"] == 1 and len(recovered_v1["seeds"]) == 2,
        "incomplete_staged_snapshot_not_activated": recovered_after_incomplete["recovered_version"] == 1,
        "complete_commit_activates_v2": recovered_v2["recovered_version"] == 2 and len(recovered_v2["seeds"]) == 3,
        "corrupt_current_falls_back_to_v1": recovered_after_corrupt["recovered_version"] == 1,
        "fallback_error_recorded": bool(recovered_after_corrupt.get("fallback_errors")),
    }
    status = "PASS_BALLOONDB_BINARY_TRANSACTION_ATOMIC_COMMIT_V00M1" if all(checks.values()) else "NO_GO_BALLOONDB_BINARY_TRANSACTION_ATOMIC_COMMIT_V00M1"

    report = {
        "status": status,
        "version": "V00M1_FIX_TRANSACTION_AND_PRODUCT_GATE",
        "db_root": str(db),
        "checks": checks,
        "current_after_corruption_recovered_version": recovered_after_corrupt["recovered_version"],
        "corrupt_path": corrupt_path,
        "fallback_errors": recovered_after_corrupt.get("fallback_errors", []),
    }
    (audit / "V00M1_TRANSACTION_SELFTEST_REPORT.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(status)
    return 0 if status.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
