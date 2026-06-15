import re
from .bql_ast import make_ast
from .bql_time_filter import parse_ts_filter, TimeFilterError

MAX_RADIUS = 3
MAX_TOP = 50

UNSAFE_WORDS = [
    "DELETE", "UPDATE", "INSERT", "WRITE", "WAL", "EXEC",
    "IMPORT", "OS", "SYSTEM", "SUBPROCESS", "VECTOR",
    "BINARY_COMPRESSION", "BINARY_COMPRESSED", "BINARY", "COMPRESSED",
    "TRANSACTION", "COMMIT", "ROLLBACK"
]
UNSAFE_CHARS = ["__", ";", "|", "&"]

class ParseError(ValueError):
    pass

def _reject_unsafe(query):
    up = query.upper()

    for token in UNSAFE_CHARS:
        if token in up:
            raise ParseError(f"unsafe token rejected: {token}")

    for token in UNSAFE_WORDS:
        pattern = r"(?<![A-Z0-9_])" + re.escape(token) + r"(?![A-Z0-9_])"
        if re.search(pattern, up):
            raise ParseError(f"unsafe token rejected: {token}")

def _parse_filter(filter_text):
    if re.match(r'^\s*ts\s*(?:>|<|\bIN\b)', filter_text, flags=re.IGNORECASE):
        try:
            return parse_ts_filter(filter_text)
        except TimeFilterError as exc:
            raise ParseError(str(exc))

    if re.match(r'^\s*[A-Za-z_][A-Za-z0-9_]*\s*(?:>|<|\bIN\b)', filter_text, flags=re.IGNORECASE):
        try:
            parse_ts_filter(filter_text)
        except TimeFilterError as exc:
            raise ParseError(str(exc))

    fm = re.match(
        r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:"([^"]+)"|([A-Za-z0-9_:\-\.]+))$',
        filter_text
    )
    if not fm:
        raise ParseError("only simple equality filter or timestamp filter is supported")

    val = fm.group(2) if fm.group(2) is not None else fm.group(3)

    if fm.group(1) == "depth":
        try:
            val = int(val)
        except Exception:
            raise ParseError("depth filter must be integer")

    return {"field": fm.group(1), "op": "=", "value": val}

def _parse_return_and_top(ret_text):
    top = None

    mtop = re.search(r'\s+TOP\s+(\d+)\s*$', ret_text, flags=re.IGNORECASE)
    if mtop:
        top = int(mtop.group(1))
        if top < 1 or top > MAX_TOP:
            raise ParseError(f"TOP out of bounds: {top}; allowed 1..{MAX_TOP}")
        ret_text = ret_text[:mtop.start()].strip()

    if not ret_text:
        raise ParseError("RETURN requires fields")

    returns = []
    for field in ret_text.split(","):
        f = field.strip()
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', f):
            raise ParseError(f"invalid return field: {f}")
        returns.append(f)

    return returns, top

def parse(query_text: str) -> dict:
    if not isinstance(query_text, str) or not query_text.strip():
        raise ParseError("empty query")

    q = " ".join(query_text.strip().split())
    _reject_unsafe(q)

    if q.upper().startswith("SELECT "):
        raise ParseError("SELECT syntax not enabled in V03G6; use FROM seed(...) BALLOON ... RETURN ... TOP N")

    explain = False
    if q.upper().startswith("EXPLAIN "):
        explain = True
        q = q[8:].strip()

    m = re.match(
        r'^FROM\s+(seed|concept)\((?:"([^"]+)"|([A-Za-z0-9_:\-\.]+))\)\s+BALLOON\s+radius\s*=\s*(\d+)\s+direction\s*=\s*([a-zA-Z_]+)\s*(.*)$',
        q,
        flags=re.IGNORECASE
    )

    if not m:
        raise ParseError("unsupported BQL syntax")

    source_type = m.group(1)
    source_value = m.group(2) if m.group(2) is not None else m.group(3)
    radius = int(m.group(4))
    direction = m.group(5).lower()
    rest = m.group(6).strip()

    if radius < 1 or radius > MAX_RADIUS:
        raise ParseError(f"radius out of bounds: {radius}; allowed 1..{MAX_RADIUS}")

    if direction not in {"up", "down", "up_down", "lateral"}:
        raise ParseError(f"unsupported direction: {direction}")

    filters = []

    if rest.upper().startswith("FILTER "):
        idx = rest.upper().find(" RETURN ")
        if idx < 0:
            raise ParseError("FILTER requires RETURN")

        filter_text = rest[7:idx].strip()
        filters.append(_parse_filter(filter_text))
        ret_text = rest[idx + len(" RETURN "):].strip()

    elif rest.upper().startswith("RETURN "):
        ret_text = rest[7:].strip()

    else:
        raise ParseError("RETURN clause required")

    returns, top = _parse_return_and_top(ret_text)

    return make_ast(
        explain=explain,
        source_type=source_type.lower(),
        source_value=source_value,
        radius=radius,
        direction=direction,
        filters=filters,
        returns=returns,
        top=top
    )
