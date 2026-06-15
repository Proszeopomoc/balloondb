use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyList, PyModule};
use sha2::{Digest, Sha256};
use std::convert::TryInto;
use std::time::{SystemTime, UNIX_EPOCH};

// Legacy/lab format from V00O. Kept for backward compatibility, not the default DB format.
const BRS_MAGIC: &[u8; 4] = b"BRS1";
const BRS_VERSION: u16 = 1;
const BRS_HEADER_LEN: usize = 4 + 2 + 1 + 1 + 2 + 4 + 4 + 32;

// Python V00J format constants: python_ref/balloondb_core/binary_format_v00j.py
const V00J_VERSION: u16 = 1;
const V00J_HEADER_SIZE: usize = 64;
const V00J_RECORD_HEADER_SIZE: usize = 24;
const V00J_KIND_SEED: u16 = 1;
const V00J_KIND_BRIDGE: u16 = 2;
const V00J_KIND_WAL: u16 = 3;

fn crc32(data: &[u8]) -> u32 {
    let mut crc: u32 = 0xFFFF_FFFF;
    for &b in data {
        crc ^= b as u32;
        for _ in 0..8 {
            let mask = (crc & 1).wrapping_neg();
            crc = (crc >> 1) ^ (0xEDB8_8320 & mask);
        }
    }
    !crc
}

fn now_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

fn brs_sha256_record(kind: u8, trust: u8, logical_id: &[u8], payload: &[u8]) -> [u8; 32] {
    let mut h = Sha256::new();
    h.update(BRS_MAGIC);
    h.update(BRS_VERSION.to_le_bytes());
    h.update([kind]);
    h.update([trust]);
    h.update((logical_id.len() as u16).to_le_bytes());
    h.update((payload.len() as u32).to_le_bytes());
    h.update(logical_id);
    h.update(payload);
    let out = h.finalize();
    let mut id = [0u8; 32];
    id.copy_from_slice(&out);
    id
}

fn v00j_magic(kind: u16) -> PyResult<&'static [u8; 8]> {
    match kind {
        V00J_KIND_SEED => Ok(b"BSEEDJ00"),
        V00J_KIND_BRIDGE => Ok(b"BBRDGJ00"),
        V00J_KIND_WAL => Ok(b"BWAL0J00"),
        _ => Err(pyo3::exceptions::PyValueError::new_err(format!("unknown V00J kind: {}", kind))),
    }
}

fn v00j_kind_from_magic(magic: &[u8]) -> PyResult<u16> {
    if magic == b"BSEEDJ00" {
        Ok(V00J_KIND_SEED)
    } else if magic == b"BBRDGJ00" {
        Ok(V00J_KIND_BRIDGE)
    } else if magic == b"BWAL0J00" {
        Ok(V00J_KIND_WAL)
    } else {
        Err(pyo3::exceptions::PyValueError::new_err(format!("invalid V00J magic: {:?}", magic)))
    }
}

fn v00j_record_id(payload: &[u8]) -> u64 {
    let digest = Sha256::digest(payload);
    u64::from_le_bytes(digest[0..8].try_into().unwrap())
}

fn v00j_record_dict<'py>(
    py: Python<'py>,
    record_id: u64,
    payload_len: u32,
    crc: u32,
    flags: u32,
    reserved: u32,
    payload: &[u8],
) -> PyResult<Bound<'py, PyDict>> {
    let d = PyDict::new_bound(py);
    d.set_item("record_id", record_id)?;
    d.set_item("payload_len", payload_len)?;
    d.set_item("crc32", crc)?;
    d.set_item("flags", flags)?;
    d.set_item("reserved", reserved)?;
    d.set_item("payload", PyBytes::new_bound(py, payload))?;
    Ok(d)
}

#[pyfunction]
fn rust_crc32(data: &[u8]) -> PyResult<u32> {
    Ok(crc32(data))
}

// Legacy/lab BRS1 functions. Not the default BalloonDB storage format.
#[pyfunction]
fn record_id_hex(kind: u8, trust: u8, logical_id: &str, payload: &[u8]) -> PyResult<String> {
    let id = brs_sha256_record(kind, trust, logical_id.as_bytes(), payload);
    Ok(hex::encode(id))
}

#[pyfunction]
fn encode_record<'py>(py: Python<'py>, kind: u8, trust: u8, logical_id: &str, payload: &[u8]) -> PyResult<Bound<'py, PyBytes>> {
    let logical = logical_id.as_bytes();
    if logical.len() > u16::MAX as usize {
        return Err(pyo3::exceptions::PyValueError::new_err("logical_id too long"));
    }
    let id = brs_sha256_record(kind, trust, logical, payload);
    let mut body = Vec::with_capacity(logical.len() + payload.len());
    body.extend_from_slice(logical);
    body.extend_from_slice(payload);
    let body_crc = crc32(&body);

    let mut out = Vec::with_capacity(BRS_HEADER_LEN + body.len());
    out.extend_from_slice(BRS_MAGIC);
    out.extend_from_slice(&BRS_VERSION.to_le_bytes());
    out.push(kind);
    out.push(trust);
    out.extend_from_slice(&(logical.len() as u16).to_le_bytes());
    out.extend_from_slice(&(payload.len() as u32).to_le_bytes());
    out.extend_from_slice(&body_crc.to_le_bytes());
    out.extend_from_slice(&id);
    out.extend_from_slice(&body);
    Ok(PyBytes::new_bound(py, &out))
}

#[pyfunction]
fn decode_record<'py>(py: Python<'py>, data: &[u8]) -> PyResult<Bound<'py, PyDict>> {
    if data.len() < BRS_HEADER_LEN {
        return Err(pyo3::exceptions::PyValueError::new_err("record too short"));
    }
    if &data[0..4] != BRS_MAGIC {
        return Err(pyo3::exceptions::PyValueError::new_err("bad magic"));
    }
    let version = u16::from_le_bytes([data[4], data[5]]);
    if version != BRS_VERSION {
        return Err(pyo3::exceptions::PyValueError::new_err("unsupported version"));
    }
    let kind = data[6];
    let trust = data[7];
    let logical_len = u16::from_le_bytes([data[8], data[9]]) as usize;
    let payload_len = u32::from_le_bytes([data[10], data[11], data[12], data[13]]) as usize;
    let stored_crc = u32::from_le_bytes([data[14], data[15], data[16], data[17]]);
    let id_bytes = &data[18..50];
    let expected_len = BRS_HEADER_LEN + logical_len + payload_len;
    if data.len() != expected_len {
        return Err(pyo3::exceptions::PyValueError::new_err(format!("bad length: {} != {}", data.len(), expected_len)));
    }
    let body = &data[BRS_HEADER_LEN..];
    let actual_crc = crc32(body);
    if actual_crc != stored_crc {
        return Err(pyo3::exceptions::PyValueError::new_err(format!("CRC mismatch: {} != {}", actual_crc, stored_crc)));
    }
    let logical = &body[..logical_len];
    let payload = &body[logical_len..];
    let recomputed = brs_sha256_record(kind, trust, logical, payload);
    if recomputed.as_slice() != id_bytes {
        return Err(pyo3::exceptions::PyValueError::new_err("record_id mismatch"));
    }

    let d = PyDict::new_bound(py);
    d.set_item("version", version)?;
    d.set_item("kind", kind)?;
    d.set_item("trust", trust)?;
    d.set_item("logical_id", String::from_utf8_lossy(logical).to_string())?;
    d.set_item("payload", PyBytes::new_bound(py, payload))?;
    d.set_item("crc32", stored_crc)?;
    d.set_item("record_id_hex", hex::encode(id_bytes))?;
    Ok(d)
}

// V00J drop-in compatible record functions.
#[pyfunction]
fn v00j_record_id_u64(payload: &[u8]) -> PyResult<u64> {
    Ok(v00j_record_id(payload))
}

#[pyfunction(signature = (payload, flags=0))]
fn v00j_encode_record<'py>(py: Python<'py>, payload: &[u8], flags: u32) -> PyResult<Bound<'py, PyBytes>> {
    let rid = v00j_record_id(payload);
    let payload_len = payload.len();
    if payload_len > u32::MAX as usize {
        return Err(pyo3::exceptions::PyValueError::new_err("payload too large"));
    }
    let crc = crc32(payload);
    let mut out = Vec::with_capacity(V00J_RECORD_HEADER_SIZE + payload_len);
    out.extend_from_slice(&rid.to_le_bytes());
    out.extend_from_slice(&(payload_len as u32).to_le_bytes());
    out.extend_from_slice(&crc.to_le_bytes());
    out.extend_from_slice(&flags.to_le_bytes());
    out.extend_from_slice(&0u32.to_le_bytes());
    out.extend_from_slice(payload);
    Ok(PyBytes::new_bound(py, &out))
}

#[pyfunction]
fn v00j_decode_record<'py>(py: Python<'py>, data: &[u8]) -> PyResult<Bound<'py, PyDict>> {
    if data.len() < V00J_RECORD_HEADER_SIZE {
        return Err(pyo3::exceptions::PyValueError::new_err("truncated V00J record header"));
    }
    let record_id = u64::from_le_bytes(data[0..8].try_into().unwrap());
    let payload_len = u32::from_le_bytes(data[8..12].try_into().unwrap());
    let expected_crc = u32::from_le_bytes(data[12..16].try_into().unwrap());
    let flags = u32::from_le_bytes(data[16..20].try_into().unwrap());
    let reserved = u32::from_le_bytes(data[20..24].try_into().unwrap());
    let expected_len = V00J_RECORD_HEADER_SIZE + payload_len as usize;
    if data.len() != expected_len {
        return Err(pyo3::exceptions::PyValueError::new_err(format!("bad V00J record length: {} != {}", data.len(), expected_len)));
    }
    let payload = &data[V00J_RECORD_HEADER_SIZE..];
    let actual_crc = crc32(payload);
    if actual_crc != expected_crc {
        return Err(pyo3::exceptions::PyValueError::new_err(format!("CRC mismatch: {} != {}", actual_crc, expected_crc)));
    }
    let calculated = v00j_record_id(payload);
    if calculated != record_id {
        return Err(pyo3::exceptions::PyValueError::new_err(format!("record id mismatch: {} != {}", calculated, record_id)));
    }
    v00j_record_dict(py, record_id, payload_len, expected_crc, flags, reserved, payload)
}

#[pyfunction(signature = (kind, record_count, created_ms=0))]
fn v00j_pack_file_header<'py>(py: Python<'py>, kind: u16, record_count: u64, created_ms: u64) -> PyResult<Bound<'py, PyBytes>> {
    let magic = v00j_magic(kind)?;
    let created = if created_ms == 0 { now_ms() } else { created_ms };
    let mut out = Vec::with_capacity(V00J_HEADER_SIZE);
    out.extend_from_slice(magic);
    out.extend_from_slice(&V00J_VERSION.to_le_bytes());
    out.extend_from_slice(&kind.to_le_bytes());
    out.extend_from_slice(&(V00J_HEADER_SIZE as u32).to_le_bytes());
    out.extend_from_slice(&created.to_le_bytes());
    out.extend_from_slice(&record_count.to_le_bytes());
    out.extend_from_slice(&[0u8; 32]);
    Ok(PyBytes::new_bound(py, &out))
}

#[pyfunction]
fn v00j_decode_file_header<'py>(py: Python<'py>, data: &[u8]) -> PyResult<Bound<'py, PyDict>> {
    if data.len() != V00J_HEADER_SIZE {
        return Err(pyo3::exceptions::PyValueError::new_err("invalid V00J file header length"));
    }
    let magic = &data[0..8];
    let version = u16::from_le_bytes(data[8..10].try_into().unwrap());
    let kind = u16::from_le_bytes(data[10..12].try_into().unwrap());
    let header_size = u32::from_le_bytes(data[12..16].try_into().unwrap());
    let created_ms = u64::from_le_bytes(data[16..24].try_into().unwrap());
    let record_count = u64::from_le_bytes(data[24..32].try_into().unwrap());
    let kind_from_magic = v00j_kind_from_magic(magic)?;
    if version != V00J_VERSION {
        return Err(pyo3::exceptions::PyValueError::new_err(format!("unsupported V00J version: {}", version)));
    }
    if kind != kind_from_magic {
        return Err(pyo3::exceptions::PyValueError::new_err("V00J kind/magic mismatch"));
    }
    if header_size as usize != V00J_HEADER_SIZE {
        return Err(pyo3::exceptions::PyValueError::new_err(format!("invalid V00J header_size: {}", header_size)));
    }
    let d = PyDict::new_bound(py);
    d.set_item("magic", String::from_utf8_lossy(magic).to_string())?;
    d.set_item("version", version)?;
    d.set_item("kind", kind)?;
    d.set_item("header_size", header_size)?;
    d.set_item("created_ms", created_ms)?;
    d.set_item("record_count", record_count)?;
    Ok(d)
}

#[pyfunction(signature = (kind, payloads, created_ms=0))]
fn v00j_encode_file<'py>(py: Python<'py>, kind: u16, payloads: Vec<Vec<u8>>, created_ms: u64) -> PyResult<Bound<'py, PyBytes>> {
    let header = v00j_pack_file_header(py, kind, payloads.len() as u64, created_ms)?;
    let mut out = Vec::new();
    out.extend_from_slice(header.as_bytes());
    for payload in payloads {
        let rec = v00j_encode_record(py, &payload, 0)?;
        out.extend_from_slice(rec.as_bytes());
    }
    Ok(PyBytes::new_bound(py, &out))
}

#[pyfunction(signature = (data, expected_kind=0))]
fn v00j_decode_file<'py>(py: Python<'py>, data: &[u8], expected_kind: u16) -> PyResult<Bound<'py, PyDict>> {
    if data.len() < V00J_HEADER_SIZE {
        return Err(pyo3::exceptions::PyValueError::new_err("V00J file too short"));
    }
    let header = v00j_decode_file_header(py, &data[..V00J_HEADER_SIZE])?;
    let kind: u16 = header.get_item("kind")?.unwrap().extract()?;
    if expected_kind != 0 && kind != expected_kind {
        return Err(pyo3::exceptions::PyValueError::new_err(format!("unexpected V00J kind: {} != {}", kind, expected_kind)));
    }
    let record_count: u64 = header.get_item("record_count")?.unwrap().extract()?;
    let records = PyList::empty_bound(py);
    let mut offset = V00J_HEADER_SIZE;
    for index in 0..record_count {
        if data.len() < offset + V00J_RECORD_HEADER_SIZE {
            return Err(pyo3::exceptions::PyValueError::new_err(format!("truncated V00J record header at index {}", index)));
        }
        let payload_len = u32::from_le_bytes(data[offset + 8..offset + 12].try_into().unwrap()) as usize;
        let end = offset + V00J_RECORD_HEADER_SIZE + payload_len;
        if data.len() < end {
            return Err(pyo3::exceptions::PyValueError::new_err(format!("truncated V00J payload at index {}", index)));
        }
        let rec = v00j_decode_record(py, &data[offset..end])?;
        records.append(rec)?;
        offset = end;
    }
    if offset != data.len() {
        return Err(pyo3::exceptions::PyValueError::new_err("unexpected V00J trailing bytes"));
    }
    let out = PyDict::new_bound(py);
    out.set_item("header", header)?;
    out.set_item("records", records)?;
    Ok(out)
}

#[pymodule]
fn balloondb_core_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Existing V00O BRS1/lab functions.
    m.add_function(wrap_pyfunction!(rust_crc32, m)?)?;
    m.add_function(wrap_pyfunction!(record_id_hex, m)?)?;
    m.add_function(wrap_pyfunction!(encode_record, m)?)?;
    m.add_function(wrap_pyfunction!(decode_record, m)?)?;

    // New V00O3 drop-in V00J compatibility functions.
    m.add_function(wrap_pyfunction!(v00j_record_id_u64, m)?)?;
    m.add_function(wrap_pyfunction!(v00j_encode_record, m)?)?;
    m.add_function(wrap_pyfunction!(v00j_decode_record, m)?)?;
    m.add_function(wrap_pyfunction!(v00j_pack_file_header, m)?)?;
    m.add_function(wrap_pyfunction!(v00j_decode_file_header, m)?)?;
    m.add_function(wrap_pyfunction!(v00j_encode_file, m)?)?;
    m.add_function(wrap_pyfunction!(v00j_decode_file, m)?)?;
    Ok(())
}