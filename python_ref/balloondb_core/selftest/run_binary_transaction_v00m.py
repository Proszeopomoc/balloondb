#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from balloondb_core.binary_transaction_v00m import BinaryAtomicStore


def resolve_repo_root() -> Path:
    here = Path(__file__).resolve()
    return here.parents[3]


def main() -> int:
    repo = resolve_repo_root()
    data_root = repo / "python_ref" / "balloondb_core" / "data" / "v00m_transaction_selftest"
    audit_root = repo / "audit" / "v00m"
    if data_root.exists():
        shutil.rmtree(data_root)
    data_root.mkdir(parents=True, exist_ok=True)
    audit_root.mkdir(parents=True, exist_ok=True)

    store = BinaryAtomicStore(data_root / "atomic_store")

    v1 = store.commit(
        seed_records=[{"logical_id": "seed.alpha", "type": "concept", "trust_state": "VERIFIED", "payload": "alpha"}],
        bridge_records=[{"logical_id": "bridge.alpha", "relation": "SELF", "trust_state": "VERIFIED"}],
        index_records=[{"key": "type:concept", "record_id": "seed.alpha"}],
        wal_records=[{"op": "insert", "record_id": "seed.alpha"}],
        version_id="v1-good",
    )
    rec1 = store.recover()
    seeds1 = store.read_current_records("snapshot.bseed")

    staged = store.stage_without_pointer(
        seed_records=[{"logical_id": "seed.beta", "type": "concept", "trust_state": "CANDIDATE", "payload": "beta"}],
        bridge_records=[],
        index_records=[{"key": "type:concept", "record_id": "seed.beta"}],
        wal_records=[{"op": "insert", "record_id": "seed.beta"}],
        version_id="v2-staged-no-pointer",
    )
    rec_after_staged = store.recover()
    seeds_after_staged = store.read_current_records("snapshot.bseed")

    v2 = store.commit(
        seed_records=[{"logical_id": "seed.beta", "type": "concept", "trust_state": "PROMOTED", "payload": "beta"}],
        bridge_records=[{"logical_id": "bridge.beta", "relation": "NEXT", "trust_state": "PROMOTED"}],
        index_records=[{"key": "trust_state:PROMOTED", "record_id": "seed.beta"}],
        wal_records=[{"op": "insert", "record_id": "seed.beta"}, {"op": "promote", "record_id": "seed.beta"}],
        version_id="v2-good",
    )
    rec2 = store.recover()
    seeds2 = store.read_current_records("snapshot.bseed")

    # Corrupt current version and verify recovery falls back to v1-good.
    current_seed = data_root / "atomic_store" / "versions" / "v2-good" / "snapshot.bseed"
    b = bytearray(current_seed.read_bytes())
    b[-1] ^= 0x55
    current_seed.write_bytes(bytes(b))
    rec_corrupt = store.recover()
    seeds_after_corrupt = store.read_current_records("snapshot.bseed")

    checks = {
        "initial_commit_ok": v1["status"] == "COMMIT_OK" and rec1.recovered_version == "v1-good" and seeds1[0]["logical_id"] == "seed.alpha",
        "staged_without_pointer_not_current": staged == "v2-staged-no-pointer" and rec_after_staged.recovered_version == "v1-good" and seeds_after_staged[0]["logical_id"] == "seed.alpha",
        "second_commit_ok": v2["status"] == "COMMIT_OK" and rec2.recovered_version == "v2-good" and seeds2[0]["logical_id"] == "seed.beta",
        "corrupt_current_fallback_used": rec_corrupt.status == "RECOVERY_FALLBACK_OK" and rec_corrupt.fallback_used is True,
        "corrupt_current_fallback_to_previous_good": rec_corrupt.recovered_version == "v1-good" and seeds_after_corrupt[0]["logical_id"] == "seed.alpha",
    }
    report = {
        "status": "PASS_BALLOONDB_BINARY_TRANSACTION_ATOMIC_COMMIT_V00M" if all(checks.values()) else "NO_GO_BALLOONDB_BINARY_TRANSACTION_ATOMIC_COMMIT_V00M",
        "version": "V00M_BINARY_TRANSACTION_AND_ATOMIC_COMMIT",
        "repo_root": str(repo),
        "data_root": str(data_root),
        "audit_root": str(audit_root),
        "checks": checks,
        "recovery": {
            "rec1": rec1.__dict__,
            "after_staged": rec_after_staged.__dict__,
            "rec2": rec2.__dict__,
            "after_corrupt": rec_corrupt.__dict__,
        },
    }
    (audit_root / "V00M_BINARY_TRANSACTION_ATOMIC_COMMIT_REPORT.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if not report["status"].startswith("PASS"):
        return 1
    print("PASS_BALLOONDB_BINARY_TRANSACTION_ATOMIC_COMMIT_V00M")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
