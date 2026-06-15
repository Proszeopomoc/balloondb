use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyModule};
use sha2::{Digest, Sha256};

const MAGIC: &[u8; 4] = b"BRS1";
const VERSION: u16 = 1;
const HEADER_LEN: usize = 4 + 2 + 1 + 1 + 2 + 4 + 4 + 32;

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

fn sha256_record(kind: u8, trust: u8, logical_id: &[u8], payload: &[u8]) -> [u8; 32] {
    let mut h = Sha256::new();
    h.update(MAGIC);
    h.update(VERSION.to_le_bytes());
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

#[pyfunction]
fn rust_crc32(data: &[u8]) -> PyResult<u32> {
    Ok(crc32(data))
}

#[pyfunction]
fn record_id_hex(kind: u8, trust: u8, logical_id: &str, payload: &[u8]) -> PyResult<String> {
    let id = sha256_record(kind, trust, logical_id.as_bytes(), payload);
    Ok(hex::encode(id))
}

#[pyfunction]
fn encode_record<'py>(py: Python<'py>, kind: u8, trust: u8, logical_id: &str, payload: &[u8]) -> PyResult<Bound<'py, PyBytes>> {
    let logical = logical_id.as_bytes();
    if logical.len() > u16::MAX as usize {
        return Err(pyo3::exceptions::PyValueError::new_err("logical_id too long"));
    }
    let id = sha256_record(kind, trust, logical, payload);
    let mut body = Vec::with_capacity(logical.len() + payload.len());
    body.extend_from_slice(logical);
    body.extend_from_slice(payload);
    let body_crc = crc32(&body);

    let mut out = Vec::with_capacity(HEADER_LEN + body.len());
    out.extend_from_slice(MAGIC);
    out.extend_from_slice(&VERSION.to_le_bytes());
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
    if data.len() < HEADER_LEN {
        return Err(pyo3::exceptions::PyValueError::new_err("record too short"));
    }
    if &data[0..4] != MAGIC {
        return Err(pyo3::exceptions::PyValueError::new_err("bad magic"));
    }
    let version = u16::from_le_bytes([data[4], data[5]]);
    if version != VERSION {
        return Err(pyo3::exceptions::PyValueError::new_err("unsupported version"));
    }
    let kind = data[6];
    let trust = data[7];
    let logical_len = u16::from_le_bytes([data[8], data[9]]) as usize;
    let payload_len = u32::from_le_bytes([data[10], data[11], data[12], data[13]]) as usize;
    let stored_crc = u32::from_le_bytes([data[14], data[15], data[16], data[17]]);
    let id_bytes = &data[18..50];
    let expected_len = HEADER_LEN + logical_len + payload_len;
    if data.len() != expected_len {
        return Err(pyo3::exceptions::PyValueError::new_err(format!("bad length: {} != {}", data.len(), expected_len)));
    }
    let body = &data[HEADER_LEN..];
    let actual_crc = crc32(body);
    if actual_crc != stored_crc {
        return Err(pyo3::exceptions::PyValueError::new_err(format!("CRC mismatch: {} != {}", actual_crc, stored_crc)));
    }
    let logical = &body[..logical_len];
    let payload = &body[logical_len..];
    let recomputed = sha256_record(kind, trust, logical, payload);
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

#[pymodule]
fn balloondb_core_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(rust_crc32, m)?)?;
    m.add_function(wrap_pyfunction!(record_id_hex, m)?)?;
    m.add_function(wrap_pyfunction!(encode_record, m)?)?;
    m.add_function(wrap_pyfunction!(decode_record, m)?)?;
    Ok(())
}
