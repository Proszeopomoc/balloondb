from __future__ import annotations

import bisect
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Sequence, Tuple

LAST_HOUR_MS = 60 * 60 * 1000


@dataclass(frozen=True)
class TSIndex:
    """Read-only in-memory timestamp index.

    ts_ms and refs are parallel sorted tuples. refs are caller-owned references:
    JSONL builders use (line_number, byte_offset); record builders use list positions.
    """

    ts_ms: Tuple[int, ...]
    refs: Tuple[Any, ...]
    ts_field: str = "ts"

    def __len__(self) -> int:
        return len(self.ts_ms)


def parse_ts_ms(value: Any) -> Optional[int]:
    """Parse a timestamp into epoch milliseconds.

    Compatible with numeric millisecond timestamps used by the V03G6 time filter and
    tolerant of ISO-8601 strings. Invalid values fail closed by returning None.
    """

    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            return None
        return int(value)

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
                return int(text)
            as_float = float(text)
            if as_float == as_float and as_float not in (float("inf"), float("-inf")):
                return int(as_float)
        except Exception:
            pass
        try:
            iso = text
            if iso.endswith("Z"):
                iso = iso[:-1] + "+00:00"
            dt = datetime.fromisoformat(iso)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp() * 1000)
        except Exception:
            return None

    return None


def _sorted_index(pairs: Iterable[Tuple[int, Any]], ts_field: str = "ts") -> TSIndex:
    ordered = sorted(pairs, key=lambda item: (item[0], repr(item[1])))
    return TSIndex(tuple(ts for ts, _ref in ordered), tuple(ref for _ts, ref in ordered), ts_field=ts_field)


def build_index_from_jsonl(path: Any, ts_field: str = "ts") -> TSIndex:
    """Build a read-only timestamp index from JSONL.

    Source data is never written. Rows with malformed JSON or invalid/missing
    timestamps are skipped so index construction fails closed for unindexable rows.
    """

    p = Path(path)
    pairs = []
    with p.open("rb") as fh:
        line_no = 0
        while True:
            offset = fh.tell()
            raw = fh.readline()
            if not raw:
                break
            line_no += 1
            try:
                row = json.loads(raw.decode("utf-8-sig"))
            except Exception:
                continue
            if not isinstance(row, dict):
                continue
            ts = parse_ts_ms(row.get(ts_field))
            if ts is None:
                continue
            pairs.append((ts, (line_no, offset)))
    return _sorted_index(pairs, ts_field=ts_field)


def build_index_from_records(records: Sequence[Any], ts_getter: Optional[Callable[[Any], Any]] = None) -> TSIndex:
    """Build a read-only timestamp index for already-expanded executor records."""

    pairs = []
    getter = ts_getter or (lambda rec: rec.get("ts") if isinstance(rec, dict) else None)
    for pos, rec in enumerate(records):
        try:
            raw_ts = getter(rec)
        except Exception:
            raw_ts = None
        ts = parse_ts_ms(raw_ts)
        if ts is None:
            continue
        pairs.append((ts, pos))
    return _sorted_index(pairs, ts_field="ts")


def range_lookup(index: TSIndex, gt: Any = None, lt: Any = None, window: Optional[str] = None, now_ms: Optional[int] = None) -> Tuple[Any, ...]:
    """Return refs matching exclusive timestamp bounds.

    gt uses bisect_right for ts > gt. lt uses bisect_left for ts < lt. The V03G6
    named window 'last_hour' is represented as an exclusive lower bound of
    now_ms - one hour.
    """

    lower = parse_ts_ms(gt) if gt is not None else None
    upper = parse_ts_ms(lt) if lt is not None else None

    if window is not None:
        if window != "last_hour":
            return tuple()
        effective_now = int(now_ms) if now_ms is not None else int(datetime.now(tz=timezone.utc).timestamp() * 1000)
        window_lower = effective_now - LAST_HOUR_MS
        lower = window_lower if lower is None else max(lower, window_lower)

    left = 0 if lower is None else bisect.bisect_right(index.ts_ms, lower)
    right = len(index.ts_ms) if upper is None else bisect.bisect_left(index.ts_ms, upper)
    if right < left:
        return tuple()
    return tuple(index.refs[left:right])


def is_supported_ts_filter(filter_obj: Any) -> bool:
    if not isinstance(filter_obj, dict):
        return False
    if filter_obj.get("field") != "ts":
        return False
    op = filter_obj.get("op")
    if op in {">", "<"}:
        return True
    return op == "in_window" and filter_obj.get("window") == "last_hour"


def refs_for_filters(index: TSIndex, filters: Sequence[Any], now_ms: Optional[int] = None) -> Tuple[Any, ...]:
    """Return candidate refs for supported timestamp filters.

    Unsupported non-timestamp predicates are ignored here and must still be checked
    by the caller. Multiple supported timestamp predicates are intersected.
    """

    supported = [f for f in (filters or []) if is_supported_ts_filter(f)]
    if not supported:
        return tuple(index.refs)

    current = set(index.refs)
    for filt in supported:
        op = filt.get("op")
        if op == ">":
            refs = set(range_lookup(index, gt=filt.get("value"), now_ms=now_ms))
        elif op == "<":
            refs = set(range_lookup(index, lt=filt.get("value"), now_ms=now_ms))
        elif op == "in_window" and filt.get("window") == "last_hour":
            refs = set(range_lookup(index, window="last_hour", now_ms=now_ms))
        else:
            refs = set()
        current &= refs
    return tuple(ref for ref in index.refs if ref in current)


def resolve_jsonl_refs(path: Any, refs: Sequence[Any]) -> list:
    """Resolve JSONL refs for selftests. This helper is read-only."""

    p = Path(path)
    wanted_lines = {int(ref[0]) for ref in refs if isinstance(ref, (tuple, list)) and len(ref) >= 1}
    rows = []
    if not wanted_lines:
        return rows
    with p.open("r", encoding="utf-8-sig") as fh:
        for line_no, line in enumerate(fh, start=1):
            if line_no not in wanted_lines:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            rows.append(obj)
    return rows
