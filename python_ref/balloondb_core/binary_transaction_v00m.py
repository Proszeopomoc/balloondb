#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""BalloonDB V00M binary transaction and atomic commit reference layer.

This module is intentionally small and deterministic.  It implements an
append-free versioned commit protocol around binary store files.  A commit is
not considered live until a CURRENT pointer is atomically replaced.  Recovery
uses the latest complete, checksum-valid version and can fall back from a
corrupted current version to a previous complete version.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
import time
import uuid
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

MAGIC_BLOB = b"BDBV00M\x00"
VERSION = 1
HEADER = struct.Struct("<8sIQQ")  # magic, version, payload_len, crc32

STORE_FILES = ("snapshot.bseed", "snapshot.bbridge", "snapshot.bindex", "snapshot.bwal")


def _fsync_file(path: Path) -> None:
    with path.open("rb") as f:
        try:
            os.fsync(f.fileno())
        except OSError:
            pass


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp.{uuid.uuid4().hex}")
    with tmp.open("wb") as f:
        f.write(data)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass
    os.replace(tmp, path)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_blob(path: Path, records: Iterable[dict]) -> Dict[str, object]:
    payload = json.dumps(list(records), sort_keys=True, separators=(",", ":")).encode("utf-8")
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    data = HEADER.pack(MAGIC_BLOB, VERSION, len(payload), crc) + payload
    _atomic_write(path, data)
    return {"path": path.name, "bytes": len(data), "payload_bytes": len(payload), "sha256": _sha256_bytes(data), "crc32": crc}


def read_blob(path: Path) -> List[dict]:
    data = path.read_bytes()
    if len(data) < HEADER.size:
        raise ValueError(f"blob too small: {path}")
    magic, version, payload_len, crc_expected = HEADER.unpack(data[:HEADER.size])
    if magic != MAGIC_BLOB:
        raise ValueError(f"bad magic: {path}")
    if version != VERSION:
        raise ValueError(f"bad version: {version}")
    payload = data[HEADER.size:HEADER.size + payload_len]
    if len(payload) != payload_len:
        raise ValueError(f"payload length mismatch: {path}")
    crc_actual = zlib.crc32(payload) & 0xFFFFFFFF
    if crc_actual != crc_expected:
        raise ValueError(f"CRC mismatch: {crc_actual} != {crc_expected}")
    return json.loads(payload.decode("utf-8"))


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class RecoveryResult:
    status: str
    current_version: Optional[str]
    recovered_version: Optional[str]
    fallback_used: bool
    reason: str


class BinaryAtomicStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.versions = self.root / "versions"
        self.staging = self.root / "staging"
        self.current = self.root / "CURRENT"
        self.versions.mkdir(parents=True, exist_ok=True)
        self.staging.mkdir(parents=True, exist_ok=True)

    def _new_version_id(self, prefix: str = "v") -> str:
        return f"{prefix}-{time.time_ns()}-{uuid.uuid4().hex[:12]}"

    def _write_version(self, target: Path, version_id: str, seed_records: List[dict], bridge_records: List[dict], index_records: List[dict], wal_records: List[dict]) -> dict:
        target.mkdir(parents=True, exist_ok=False)
        files = {}
        files["snapshot.bseed"] = write_blob(target / "snapshot.bseed", seed_records)
        files["snapshot.bbridge"] = write_blob(target / "snapshot.bbridge", bridge_records)
        files["snapshot.bindex"] = write_blob(target / "snapshot.bindex", index_records)
        files["snapshot.bwal"] = write_blob(target / "snapshot.bwal", wal_records)
        manifest = {
            "magic": "BDBM_V00M",
            "version": "V00M_BINARY_TRANSACTION_ATOMIC_COMMIT",
            "version_id": version_id,
            "created_ns": time.time_ns(),
            "files": {name: {"sha256": file_sha256(target / name), "bytes": (target / name).stat().st_size} for name in STORE_FILES},
            "record_counts": {
                "seed": len(seed_records),
                "bridge": len(bridge_records),
                "index": len(index_records),
                "wal": len(wal_records),
            },
        }
        _atomic_write(target / "snapshot.bdbm", json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8"))
        _atomic_write(target / "SNAPSHOT_COMPLETE", b"SNAPSHOT_COMPLETE\n")
        return manifest

    def commit(self, seed_records: List[dict], bridge_records: List[dict], index_records: List[dict], wal_records: List[dict], *, version_id: Optional[str] = None) -> dict:
        version_id = version_id or self._new_version_id()
        tmp = self.staging / (version_id + ".tmp")
        final = self.versions / version_id
        if tmp.exists():
            shutil.rmtree(tmp)
        if final.exists():
            shutil.rmtree(final)
        manifest = self._write_version(tmp, version_id, seed_records, bridge_records, index_records, wal_records)
        tmp.rename(final)
        _atomic_write(self.current, (version_id + "\n").encode("ascii"))
        return {"status": "COMMIT_OK", "version_id": version_id, "manifest": manifest}

    def stage_without_pointer(self, seed_records: List[dict], bridge_records: List[dict], index_records: List[dict], wal_records: List[dict], *, version_id: Optional[str] = None) -> str:
        version_id = version_id or self._new_version_id("staged")
        final = self.versions / version_id
        if final.exists():
            shutil.rmtree(final)
        self._write_version(final, version_id, seed_records, bridge_records, index_records, wal_records)
        return version_id

    def _validate_version(self, version_dir: Path) -> Tuple[bool, str]:
        try:
            if not (version_dir / "SNAPSHOT_COMPLETE").exists():
                return False, "missing SNAPSHOT_COMPLETE"
            manifest_path = version_dir / "snapshot.bdbm"
            if not manifest_path.exists():
                return False, "missing manifest"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("version_id") != version_dir.name:
                return False, "manifest version_id mismatch"
            for name in STORE_FILES:
                p = version_dir / name
                if not p.exists():
                    return False, f"missing {name}"
                expected = manifest["files"][name]["sha256"]
                actual = file_sha256(p)
                if actual != expected:
                    return False, f"sha256 mismatch {name}"
                read_blob(p)  # includes CRC validation
            return True, "ok"
        except Exception as e:
            return False, repr(e)

    def recover(self) -> RecoveryResult:
        current_id = None
        if self.current.exists():
            current_id = self.current.read_text(encoding="ascii", errors="replace").strip() or None
        if current_id:
            ok, reason = self._validate_version(self.versions / current_id)
            if ok:
                return RecoveryResult("RECOVERY_OK", current_id, current_id, False, reason)
        candidates = []
        for d in self.versions.iterdir() if self.versions.exists() else []:
            if d.is_dir():
                ok, reason = self._validate_version(d)
                if ok:
                    try:
                        manifest = json.loads((d / "snapshot.bdbm").read_text(encoding="utf-8"))
                        candidates.append((int(manifest.get("created_ns", 0)), d.name))
                    except Exception:
                        candidates.append((0, d.name))
        if not candidates:
            return RecoveryResult("NO_VALID_SNAPSHOT", current_id, None, False, "no valid complete version")
        candidates.sort()
        recovered = candidates[-1][1]
        _atomic_write(self.current, (recovered + "\n").encode("ascii"))
        return RecoveryResult("RECOVERY_FALLBACK_OK", current_id, recovered, True, "fallback to latest valid complete snapshot")

    def read_current_records(self, filename: str) -> List[dict]:
        result = self.recover()
        if not result.recovered_version:
            raise RuntimeError("no recovered version")
        return read_blob(self.versions / result.recovered_version / filename)
