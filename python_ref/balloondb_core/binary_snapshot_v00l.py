from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

from balloondb_core.binary_format_v00j import (
    BalloonBinaryChecksumError,
    BalloonBinaryFormatError,
    read_bbridge,
    read_bseed,
    replay_bwal,
    sha256_file,
    verify_records,
    write_bbridge,
    write_bseed,
    write_manifest,
)
from balloondb_core.binary_index_v00k import build_index_from_files, read_index, verify_index

VERSION = "V00L_BINARY_COMPACTION_AND_SNAPSHOT"


class BalloonBinarySnapshotError(Exception):
    pass


class BalloonBinarySnapshotRecoveryError(BalloonBinarySnapshotError):
    pass


def now_ms() -> int:
    return int(time.time() * 1000)


def logical_seed_id(payload: dict[str, Any], fallback: str) -> str:
    return str(payload.get("seed_id") or payload.get("id") or payload.get("key") or fallback)


def logical_bridge_id(payload: dict[str, Any], fallback: str) -> str:
    return str(payload.get("bridge_id") or payload.get("id") or payload.get("key") or fallback)


def _load_seed_map(path: str | Path) -> dict[str, dict[str, Any]]:
    header, records = read_bseed(path)
    result: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        key = logical_seed_id(record.payload, f"rid:{record.record_id}")
        result[key] = dict(record.payload)
    return result


def _load_bridge_map(path: str | Path) -> dict[str, dict[str, Any]]:
    header, records = read_bbridge(path)
    result: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        key = logical_bridge_id(record.payload, f"rid:{record.record_id}")
        result[key] = dict(record.payload)
    return result


def _apply_wal(seed_map: dict[str, dict[str, Any]], bridge_map: dict[str, dict[str, Any]], wal_path: str | Path) -> dict[str, Any]:
    entries = replay_bwal(wal_path)
    stats = {
        "wal_entry_count": len(entries),
        "upsert_seed_count": 0,
        "upsert_bridge_count": 0,
        "delete_seed_count": 0,
        "delete_bridge_count": 0,
        "ignored_entry_count": 0,
    }
    for entry in entries:
        op = str(entry.get("op", "")).upper()
        if op == "UPSERT_SEED":
            payload = dict(entry.get("payload") or {})
            if not payload:
                stats["ignored_entry_count"] += 1
                continue
            key = logical_seed_id(payload, f"wal_seed_{stats['upsert_seed_count']}")
            seed_map[key] = payload
            stats["upsert_seed_count"] += 1
        elif op == "UPSERT_BRIDGE":
            payload = dict(entry.get("payload") or {})
            if not payload:
                stats["ignored_entry_count"] += 1
                continue
            key = logical_bridge_id(payload, f"wal_bridge_{stats['upsert_bridge_count']}")
            bridge_map[key] = payload
            stats["upsert_bridge_count"] += 1
        elif op == "DELETE_SEED":
            key = str(entry.get("logical_id") or entry.get("seed_id") or "")
            if key and key in seed_map:
                del seed_map[key]
            stats["delete_seed_count"] += 1
        elif op == "DELETE_BRIDGE":
            key = str(entry.get("logical_id") or entry.get("bridge_id") or "")
            if key and key in bridge_map:
                del bridge_map[key]
            stats["delete_bridge_count"] += 1
        else:
            stats["ignored_entry_count"] += 1
    return stats


def _atomic_replace_dir(staging_dir: Path, final_dir: Path) -> None:
    if final_dir.exists():
        backup = final_dir.with_name(final_dir.name + ".prev")
        if backup.exists():
            shutil.rmtree(backup)
        final_dir.rename(backup)
    staging_dir.rename(final_dir)


def compact_wal_to_snapshot(
    base_bseed: str | Path,
    base_bbridge: str | Path,
    wal_path: str | Path,
    snapshot_root: str | Path,
    snapshot_name: str = "snapshot_v00l",
) -> dict[str, Any]:
    base_bseed = Path(base_bseed)
    base_bbridge = Path(base_bbridge)
    wal_path = Path(wal_path)
    snapshot_root = Path(snapshot_root)
    snapshot_root.mkdir(parents=True, exist_ok=True)

    staging = snapshot_root / (snapshot_name + ".staging")
    final = snapshot_root / snapshot_name
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)

    seed_map = _load_seed_map(base_bseed)
    bridge_map = _load_bridge_map(base_bbridge)
    stats = _apply_wal(seed_map, bridge_map, wal_path)

    seeds = [seed_map[k] for k in sorted(seed_map)]
    bridges = [bridge_map[k] for k in sorted(bridge_map)]

    out_bseed = staging / "snapshot.bseed"
    out_bbridge = staging / "snapshot.bbridge"
    out_bindex = staging / "snapshot.bindex"
    out_manifest = staging / "snapshot.bdbm"
    complete_marker = staging / "SNAPSHOT_COMPLETE"

    seed_meta = write_bseed(out_bseed, seeds)
    bridge_meta = write_bbridge(out_bbridge, bridges)
    index_meta = build_index_from_files(out_bindex, out_bseed, out_bbridge)

    manifest = write_manifest(
        out_manifest,
        files=[
            {"role": "snapshot_bseed", **seed_meta},
            {"role": "snapshot_bbridge", **bridge_meta},
            {"role": "snapshot_bindex", **index_meta},
        ],
        extra={
            "format": "BALLOONDB_SNAPSHOT_V00L",
            "base_bseed_sha256": sha256_file(base_bseed),
            "base_bbridge_sha256": sha256_file(base_bbridge),
            "wal_sha256": sha256_file(wal_path),
            "wal_stats": stats,
            "seed_count_after_compaction": len(seeds),
            "bridge_count_after_compaction": len(bridges),
            "created_ms": now_ms(),
        },
    )

    complete_marker.write_text(json.dumps({"status": "SNAPSHOT_COMPLETE", "manifest_sha256": sha256_file(out_manifest)}, indent=2), encoding="utf-8")

    _atomic_replace_dir(staging, final)

    return {
        "status": "PASS_BINARY_SNAPSHOT_COMPACTED_V00L",
        "snapshot_dir": str(final),
        "seed_count": len(seeds),
        "bridge_count": len(bridges),
        "wal_stats": stats,
        "manifest": str(final / "snapshot.bdbm"),
        "manifest_sha256": sha256_file(final / "snapshot.bdbm"),
    }


def recover_snapshot(snapshot_dir: str | Path) -> dict[str, Any]:
    snapshot_dir = Path(snapshot_dir)
    manifest_path = snapshot_dir / "snapshot.bdbm"
    complete_marker = snapshot_dir / "SNAPSHOT_COMPLETE"
    bseed = snapshot_dir / "snapshot.bseed"
    bbridge = snapshot_dir / "snapshot.bbridge"
    bindex = snapshot_dir / "snapshot.bindex"

    if not complete_marker.exists():
        raise BalloonBinarySnapshotRecoveryError("missing SNAPSHOT_COMPLETE marker")
    if not manifest_path.exists():
        raise BalloonBinarySnapshotRecoveryError("missing snapshot manifest")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    verify_seed = verify_records(bseed)
    verify_bridge = verify_records(bbridge)
    verify_idx = verify_index(bindex)
    header, payload = read_index(bindex)
    seed_header, seeds = read_bseed(bseed)
    bridge_header, bridges = read_bbridge(bbridge)

    expected_count = int(manifest.get("extra", {}).get("seed_count_after_compaction", -1))
    expected_bridge_count = int(manifest.get("extra", {}).get("bridge_count_after_compaction", -1))
    if expected_count != len(seeds):
        raise BalloonBinarySnapshotRecoveryError(f"seed count mismatch: {expected_count} != {len(seeds)}")
    if expected_bridge_count != len(bridges):
        raise BalloonBinarySnapshotRecoveryError(f"bridge count mismatch: {expected_bridge_count} != {len(bridges)}")

    return {
        "status": "PASS_BINARY_SNAPSHOT_RECOVERY_V00L",
        "snapshot_dir": str(snapshot_dir),
        "seed_count": len(seeds),
        "bridge_count": len(bridges),
        "index_record_count": int(payload.get("record_count", -1)),
        "manifest_sha256": sha256_file(manifest_path),
        "verify_seed": verify_seed,
        "verify_bridge": verify_bridge,
        "verify_index": verify_idx,
        "manifest_extra": manifest.get("extra", {}),
    }


def corrupt_snapshot_seed(src_snapshot: str | Path, dst_snapshot: str | Path) -> Path:
    from balloondb_core.binary_format_v00j import HEADER_SIZE, RECORD_HEADER_SIZE

    src_snapshot = Path(src_snapshot)
    dst_snapshot = Path(dst_snapshot)
    if dst_snapshot.exists():
        shutil.rmtree(dst_snapshot)
    shutil.copytree(src_snapshot, dst_snapshot)
    target = dst_snapshot / "snapshot.bseed"
    data = bytearray(target.read_bytes())
    if len(data) <= HEADER_SIZE + RECORD_HEADER_SIZE + 2:
        raise BalloonBinarySnapshotError("snapshot bseed too small to corrupt")
    data[HEADER_SIZE + RECORD_HEADER_SIZE + 1] ^= 0x44
    target.write_bytes(bytes(data))
    return dst_snapshot
