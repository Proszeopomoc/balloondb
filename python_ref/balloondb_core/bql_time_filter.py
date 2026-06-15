import re
import time

NAMED_WINDOWS_MS = {
    "last_hour": 60 * 60 * 1000,
    "last_day": 24 * 60 * 60 * 1000,
    "last_7_days": 7 * 24 * 60 * 60 * 1000,
}

class TimeFilterError(ValueError):
    pass

def _parse_non_negative_unix_ms(text):
    if not re.fullmatch(r"[0-9]+", text or ""):
        if text and text.startswith("-"):
            raise TimeFilterError("timestamp must be non-negative unix milliseconds")
        raise TimeFilterError("timestamp must be an integer unix milliseconds value")
    value = int(text)
    if value < 0:
        raise TimeFilterError("timestamp must be non-negative unix milliseconds")
    return value

def parse_ts_filter(filter_text):
    if not isinstance(filter_text, str) or not filter_text.strip():
        raise TimeFilterError("timestamp filter is empty")

    text = filter_text.strip()

    cmp_match = re.fullmatch(r"(?i)ts\s*(>|<)\s*([^\s]+)", text)
    if cmp_match:
        op = cmp_match.group(1)
        value = _parse_non_negative_unix_ms(cmp_match.group(2))
        return {"field": "ts", "op": op, "value": value}

    in_match = re.fullmatch(r"(?i)ts\s+IN\s+([A-Za-z0-9_]+)", text)
    if in_match:
        window = in_match.group(1).lower()
        if window not in NAMED_WINDOWS_MS:
            raise TimeFilterError("unknown timestamp named window: " + in_match.group(1))
        return {"field": "ts", "op": "in_window", "window": window}

    field_match = re.match(r"(?i)^([A-Za-z_][A-Za-z0-9_]*)\b", text)
    if field_match and field_match.group(1).lower() != "ts":
        raise TimeFilterError("unsupported field for timestamp filter syntax: " + field_match.group(1))

    if re.search(r"(?i)^ts\s+IN\b", text):
        raise TimeFilterError("timestamp IN filter must use one of: last_hour, last_day, last_7_days")

    if re.search(r"(?i)^ts\s*[=!]=?|>=|<=", text):
        raise TimeFilterError("unsupported timestamp operator; supported operators are >, <, and IN")

    raise TimeFilterError("unsupported timestamp filter; expected ts > <unix_ms>, ts < <unix_ms>, or ts IN last_hour|last_day|last_7_days")

def record_ts(record_or_value):
    value = record_or_value
    if isinstance(record_or_value, dict):
        if "ts" not in record_or_value:
            return None
        value = record_or_value.get("ts")

    if isinstance(value, bool) or value is None:
        return None

    if isinstance(value, int):
        return value if value >= 0 else None

    if isinstance(value, float):
        return int(value) if value.is_integer() and value >= 0 else None

    if isinstance(value, str):
        stripped = value.strip()
        if re.fullmatch(r"[0-9]+", stripped):
            return int(stripped)
        return None

    try:
        converted = int(value)
    except Exception:
        return None
    return converted if converted >= 0 else None

def match_ts_filter(actual_ts, filter_dict, now_ms=None):
    actual = record_ts(actual_ts)
    if actual is None:
        return False

    if now_ms is None:
        now_ms = int(time.time() * 1000)
    else:
        now_ms = int(now_ms)

    op = filter_dict.get("op")
    if op == ">":
        return actual > int(filter_dict["value"])
    if op == "<":
        return actual < int(filter_dict["value"])
    if op == "in_window":
        window = filter_dict.get("window")
        if window not in NAMED_WINDOWS_MS:
            raise TimeFilterError("unknown timestamp named window: " + str(window))
        lower = now_ms - NAMED_WINDOWS_MS[window]
        return lower <= actual <= now_ms

    raise TimeFilterError("unsupported timestamp filter operator: " + str(op))
