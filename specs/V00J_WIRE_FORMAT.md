# V00J wire format — the byte spec the Rust drop-in must match (V00O3)

This is the exact on-disk format of `.bseed` / `.bbridge` / `.bwal` as implemented in
`python_ref/balloondb_core/binary_format_v00j.py`. It was reconstructed independently and
confirmed **byte-identical** to the live Python module. The Rust core must reproduce these
bytes exactly to be a true drop-in (not a parallel format).

All integers little-endian.

## File header — 64 bytes  (`struct "<8sHHIQQ32s"`)

| Field | Type | Bytes | Value |
|---|---|---|---|
| magic | 8s | 8 | `BSEEDJ00` (seed) / `BBRDGJ00` (bridge) / `BWAL0J00` (wal) |
| version | u16 | 2 | `1` |
| kind | u16 | 2 | seed=`1`, bridge=`2`, wal=`3` |
| header_size | u32 | 4 | `64` |
| created_ms | u64 | 8 | unix epoch ms |
| record_count | u64 | 8 | number of records |
| reserved | 32s | 32 | 32 zero bytes |

## Record header — 24 bytes  (`struct "<QIIII"`), then `payload_len` payload bytes

| Field | Type | Bytes | Value |
|---|---|---|---|
| record_id | u64 | 8 | first 8 bytes of `sha256(payload)`, little-endian |
| payload_len | u32 | 4 | length of payload bytes |
| crc32 | u32 | 4 | `crc32(payload)` (standard CRC-32, == zlib.crc32) |
| flags | u32 | 4 | `0` |
| reserved | u32 | 4 | `0` |

`record_id` and `crc32` are computed over the **payload bytes** (the canonical JSON below),
not over the header.

## Payload = canonical JSON  ← THE ONLY HARD PART

The payload bytes are produced by:

```python
json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
```

Rust must match this byte-for-byte. The traps:

- **Keys sorted** (recursively), ascending by Unicode code point.
- **Compact separators**: `,` and `:` with no spaces.
- **`ensure_ascii=False`**: non-ASCII is raw UTF-8, not `\uXXXX`.
- **Floats keep a decimal**: `1.0` stays `1.0`, not `1`. Ints stay ints (`1`).
- **`true` / `false` / `null`** lowercase. Arrays keep their order (NOT sorted).

### Locked golden vectors (the canonicalizer contract)

| payload | canonical bytes (hex) | record_id (u64) | crc32 |
|---|---|---|---|
| `{}` | `7b7d` | 9973137080230810436 | 2745614147 |
| `{"id":"PY_NAMEERROR","trust":"VERIFIED","n":1,"x":1.0,"y":1.5}` | `7b226964223a2250595f4e414d454552524f52222c226e223a312c227472757374223a225645524946494544222c2278223a312e302c2279223a312e357d` | 1746617285619952443 | 1188715145 |
| `{"txt":"błąd","ż":"ąćźń","nested":{"b":2,"a":[3,1,2]},"ok":true,"nil":null}` | `7b226e6573746564223a7b2261223a5b332c312c325d2c2262223a327d2c226e696c223a6e756c6c2c226f6b223a747275652c22747874223a2262c582c48564222c22c5bc223a22c485c487c5bac584227d` | 16859162784457723423 | 3856007266 |

## Recommended scoping (avoids the parity rabbit hole)

The framing (headers, sha256-id, crc, file IO) is trivially byte-exact in Rust. The JSON
canonicalization is the bug-prone part. **Strong recommendation: Rust does NOT serialize
JSON.** Rust operates on already-canonical `payload: bytes`. Canonicalization stays one
shared Python function (`canonical_payload`). Then the Rust drop-in has zero JSON-parity
risk and only has to match the (mechanical) framing.

If Rust must canonicalize itself later, gate it behind the golden vectors above and a
fuzz test that diffs Rust canon vs Python `json.dumps` across floats, unicode, nesting,
ints-vs-floats, empty, null, bools — and treat any single-byte diff as a hard fail.

## Rust API contract for V00O3 (operating on canonical payload bytes)

The acceptance test (`run_v00j_rust_compat_v00o3.py`) probes the PyO3 module for:

```text
v00j_record_id(payload: bytes) -> int
v00j_encode_record(payload: bytes) -> bytes        # 24-byte record header + payload
v00j_write_file(kind: int, created_ms: int, payloads: list[bytes]) -> bytes
v00j_read_file(data: bytes) -> dict                # {"header": {...}, "records": [{record_id, crc32, flags, payload}, ...]}
```

## Definition of done for V00O3

- Rust `v00j_write_file(...)` bytes are identical to Python `binary_format_v00j.write_records`
  (for the same `created_ms`).
- Rust `v00j_read_file(python_bytes)` returns identical records (ids, crc, payloads).
- Python `read_records(rust_bytes)` succeeds with matching ids.
- The golden vectors above reproduce exactly through the Rust path.
- BRS1 stays in `rust/` as an experimental lab format, not used by the engine.
