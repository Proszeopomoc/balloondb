from __future__ import annotations

import json
import os
import shutil
import struct
import zlib
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

SNAP_MAGIC = b"BDBSNPM1"
HEADER = struct.Struct("<8sII")  # magic, payload_len, crc32

class SnapshotCorruptError(Exception):
    pass

class NoCompleteSnapshotError(Exception):
    pass

def _json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def _write_bytes_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("wb") as f:
        f.write(data)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass
    os.replace(tmp, path)

def _write_text_atomic(path: Path, text: str) -> None:
    _write_bytes_atomic(path, text.encode("utf-8"))

def _encode_blob(payload: Any) -> bytes:
    raw = _json_bytes(payload)
    crc = zlib.crc32(raw) & 0xFFFFFFFF
    return HEADER.pack(SNAP_MAGIC, len(raw), crc) + raw

def _decode_blob(path: Path) -> Any:
    data = path.read_bytes()
    if len(data) < HEADER.size:
        raise SnapshotCorruptError(f"short file: {path}")
    magic, n, expected_crc = HEADER.unpack(data[:HEADER.size])
    if magic != SNAP_MAGIC:
        raise SnapshotCorruptError(f"bad magic: {path}")
    payload = data[HEADER.size:]
    if len(payload) != n:
        raise SnapshotCorruptError(f"bad payload length: {path}")
    actual_crc = zlib.crc32(payload) & 0xFFFFFFFF
    if actual_crc != expected_crc:
        raise SnapshotCorruptError(f"CRC mismatch: {path}: {actual_crc} != {expected_crc}")
    return json.loads(payload.decode("utf-8"))

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _version_name(version: int) -> str:
    return f"snapshot_{version:08d}"

def _snapshot_dir(root: Path, version: int) -> Path:
    return root / "snapshots" / _version_name(version)

def _read_current(root: Path) -> Optional[int]:
    p = root / "CURRENT"
    if not p.exists():
        return None
    txt = p.read_text(encoding="utf-8", errors="replace").strip()
    if txt.startswith("snapshot_"):
        return int(txt.split("_")[-1])
    return int(txt)

def _write_current_atomic(root: Path, version: int) -> None:
    _write_text_atomic(root / "CURRENT", _version_name(version) + "\n")

def build_snapshot_index(seeds: List[Dict[str, Any]], bridges: List[Dict[str, Any]]) -> Dict[str, Any]:
    seed_ids = [s.get("record_id") or s.get("id") or s.get("logical_id") for s in seeds]
    bridge_ids = [b.get("record_id") or b.get("id") or b.get("logical_id") for b in bridges]
    return {
        "seed_count": len(seeds),
        "bridge_count": len(bridges),
        "seed_ids": seed_ids,
        "bridge_ids": bridge_ids,
        "trust_states": sorted({str(x.get("trust_state", "")) for x in seeds + bridges}),
        "types": sorted({str(x.get("type", "")) for x in seeds + bridges}),
    }

def stage_snapshot(root: Path, version: int, seeds: List[Dict[str, Any]], bridges: List[Dict[str, Any]], complete: bool = True) -> Path:
    root = Path(root)
    d = _snapshot_dir(root, version)
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True, exist_ok=True)

    _write_bytes_atomic(d / "snapshot.bseed", _encode_blob({"kind": "bseed_snapshot", "records": seeds}))
    _write_bytes_atomic(d / "snapshot.bbridge", _encode_blob({"kind": "bbridge_snapshot", "records": bridges}))
    _write_bytes_atomic(d / "snapshot.bindex", _encode_blob({"kind": "bindex_snapshot", "index": build_snapshot_index(seeds, bridges)}))

    manifest = {
        "format": "BALLOONDB_BINARY_TRANSACTION_V00M1",
        "version": version,
        "files": {
            "snapshot.bseed": _sha256_file(d / "snapshot.bseed"),
            "snapshot.bbridge": _sha256_file(d / "snapshot.bbridge"),
            "snapshot.bindex": _sha256_file(d / "snapshot.bindex"),
        },
    }
    _write_text_atomic(d / "snapshot.bdbm", json.dumps(manifest, indent=2, sort_keys=True))
    if complete:
        _write_text_atomic(d / "SNAPSHOT_COMPLETE", "complete\n")
    return d

def commit_snapshot(root: Path, version: int, seeds: List[Dict[str, Any]], bridges: List[Dict[str, Any]]) -> Path:
    d = stage_snapshot(root, version, seeds, bridges, complete=True)
    # Activate only after all files and marker are present.
    _write_current_atomic(Path(root), version)
    return d

def validate_snapshot_dir(d: Path) -> Dict[str, Any]:
    if not (d / "SNAPSHOT_COMPLETE").exists():
        raise SnapshotCorruptError(f"missing SNAPSHOT_COMPLETE: {d}")
    for name in ["snapshot.bseed", "snapshot.bbridge", "snapshot.bindex", "snapshot.bdbm"]:
        if not (d / name).exists():
            raise SnapshotCorruptError(f"missing {name}: {d}")
    seeds_blob = _decode_blob(d / "snapshot.bseed")
    bridges_blob = _decode_blob(d / "snapshot.bbridge")
    index_blob = _decode_blob(d / "snapshot.bindex")
    manifest = json.loads((d / "snapshot.bdbm").read_text(encoding="utf-8"))
    for name, expected in manifest.get("files", {}).items():
        actual = _sha256_file(d / name)
        if actual != expected:
            raise SnapshotCorruptError(f"sha256 mismatch {name}: {actual} != {expected}")
    return {
        "version": manifest.get("version"),
        "seeds": seeds_blob.get("records", []),
        "bridges": bridges_blob.get("records", []),
        "index": index_blob.get("index", {}),
        "snapshot_dir": str(d),
    }

def recover_latest_complete_snapshot(root: Path) -> Dict[str, Any]:
    root = Path(root)
    candidates: List[int] = []
    cur = _read_current(root)
    if cur is not None:
        candidates.append(cur)
    snaps = root / "snapshots"
    if snaps.exists():
        for d in snaps.iterdir():
            if d.is_dir() and d.name.startswith("snapshot_"):
                try:
                    v = int(d.name.split("_")[-1])
                    if v not in candidates:
                        candidates.append(v)
                except ValueError:
                    pass
    candidates = sorted(candidates, reverse=True)
    errors = []
    for v in candidates:
        try:
            out = validate_snapshot_dir(_snapshot_dir(root, v))
            out["recovered_version"] = v
            out["fallback_errors"] = errors
            return out
        except Exception as e:
            errors.append({"version": v, "error": str(e)})
    raise NoCompleteSnapshotError(json.dumps(errors, ensure_ascii=False))

def corrupt_snapshot_seed_payload(root: Path, version: int) -> str:
    p = _snapshot_dir(Path(root), version) / "snapshot.bseed"
    data = bytearray(p.read_bytes())
    if len(data) <= HEADER.size:
        raise SnapshotCorruptError("cannot corrupt short payload")
    data[HEADER.size] ^= 0xFF
    p.write_bytes(bytes(data))
    return str(p)
