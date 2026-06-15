// v00j.rs  --  Rust drop-in for the existing BalloonDB V00J on-disk format.
//
// Operates on ALREADY-CANONICAL payload bytes (no JSON in Rust -> zero canonicalization
// parity risk; see V00J_WIRE_FORMAT.md). Byte-for-byte compatible with
// python_ref/balloondb_core/binary_format_v00j.py.
//
// To wire in: `mod v00j;` in lib.rs, and add to the #[pymodule]:
//     m.add_function(wrap_pyfunction!(v00j::v00j_record_id, m)?)?;
//     m.add_function(wrap_pyfunction!(v00j::v00j_encode_record, m)?)?;
//     m.add_function(wrap_pyfunction!(v00j::v00j_write_file, m)?)?;
//     m.add_function(wrap_pyfunction!(v00j::v00j_read_file, m)?)?;

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyList};
use sha2::{Digest, Sha256};

const HEADER_SIZE: usize = 64;
const RECORD_HEADER_SIZE: usize = 24;
const VERSION: u16 = 1;

fn magic_for_kind(kind: u16) -> PyResult<&'static [u8; 8]> {
    match kind {
        1 => Ok(b"BSEEDJ00"),
        2 => Ok(b"BBRDGJ00"),
        3 => Ok(b"BWAL0J00"),
        _ => Err(pyo3::exceptions::PyValueError::new_err(format!("unknown kind: {}", kind))),
    }
}
fn kind_for_magic(magic: &[u8]) -> PyResult<u16> {
    if magic == b"BSEEDJ00" {
        Ok(1)
    } else if magic == b"BBRDGJ00" {
        Ok(2)
    } else if magic == b"BWAL0J00" {
        Ok(3)
    } else {
        Err(pyo3::exceptions::PyValueError::new_err("invalid magic"))
    }
}

// standard CRC-32 (== zlib.crc32)
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

// record_id = first 8 bytes of sha256(payload), little-endian u64
fn record_id_le(payload: &[u8]) -> u64 {
    let d = Sha256::digest(payload);
    u64::from_le_bytes([d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7]])
}

fn push_record(out: &mut Vec<u8>, payload: &[u8]) {
    out.extend_from_slice(&record_id_le(payload).to_le_bytes());     // Q record_id
    out.extend_from_slice(&(payload.len() as u32).to_le_bytes());    // I payload_len
    out.extend_from_slice(&crc32(payload).to_le_bytes());            // I crc32
    out.extend_from_slice(&0u32.to_le_bytes());                      // I flags
    out.extend_from_slice(&0u32.to_le_bytes());                      // I reserved
    out.extend_from_slice(payload);
}

#[pyfunction]
pub fn v00j_record_id(payload: &[u8]) -> PyResult<u64> {
    Ok(record_id_le(payload))
}

#[pyfunction]
pub fn v00j_encode_record<'py>(py: Python<'py>, payload: &[u8]) -> PyResult<Bound<'py, PyBytes>> {
    let mut out = Vec::with_capacity(RECORD_HEADER_SIZE + payload.len());
    push_record(&mut out, payload);
    Ok(PyBytes::new_bound(py, &out))
}

#[pyfunction]
pub fn v00j_write_file<'py>(py: Python<'py>, kind: u16, created_ms: u64, payloads: Vec<Vec<u8>>) -> PyResult<Bound<'py, PyBytes>> {
    let magic = magic_for_kind(kind)?;
    let mut out = Vec::with_capacity(HEADER_SIZE + payloads.iter().map(|p| RECORD_HEADER_SIZE + p.len()).sum::<usize>());
    out.extend_from_slice(magic);                                   // 8s magic
    out.extend_from_slice(&VERSION.to_le_bytes());                  // H version
    out.extend_from_slice(&kind.to_le_bytes());                     // H kind
    out.extend_from_slice(&(HEADER_SIZE as u32).to_le_bytes());     // I header_size
    out.extend_from_slice(&created_ms.to_le_bytes());               // Q created_ms
    out.extend_from_slice(&(payloads.len() as u64).to_le_bytes());  // Q record_count
    out.extend_from_slice(&[0u8; 32]);                              // 32s reserved
    for p in &payloads {
        push_record(&mut out, p);
    }
    Ok(PyBytes::new_bound(py, &out))
}

#[pyfunction]
pub fn v00j_read_file<'py>(py: Python<'py>, data: &[u8]) -> PyResult<Bound<'py, PyDict>> {
    if data.len() < HEADER_SIZE {
        return Err(pyo3::exceptions::PyValueError::new_err("invalid header length"));
    }
    let magic = &data[0..8];
    let kind = kind_for_magic(magic)?;
    let version = u16::from_le_bytes([data[8], data[9]]);
    if version != VERSION {
        return Err(pyo3::exceptions::PyValueError::new_err("unsupported version"));
    }
    let kind_field = u16::from_le_bytes([data[10], data[11]]);
    if kind_field != kind {
        return Err(pyo3::exceptions::PyValueError::new_err("kind/magic mismatch"));
    }
    let header_size = u32::from_le_bytes([data[12], data[13], data[14], data[15]]);
    if header_size as usize != HEADER_SIZE {
        return Err(pyo3::exceptions::PyValueError::new_err("invalid header_size"));
    }
    let created_ms = u64::from_le_bytes(data[16..24].try_into().unwrap());
    let record_count = u64::from_le_bytes(data[24..32].try_into().unwrap());

    let header = PyDict::new_bound(py);
    header.set_item("kind", kind)?;
    header.set_item("version", version)?;
    header.set_item("created_ms", created_ms)?;
    header.set_item("record_count", record_count)?;

    let records = PyList::empty_bound(py);
    let mut pos = HEADER_SIZE;
    let mut index: u64 = 0;
    while pos < data.len() {
        if pos + RECORD_HEADER_SIZE > data.len() {
            return Err(pyo3::exceptions::PyValueError::new_err("truncated record header"));
        }
        let rid = u64::from_le_bytes(data[pos..pos + 8].try_into().unwrap());
        let payload_len = u32::from_le_bytes(data[pos + 8..pos + 12].try_into().unwrap()) as usize;
        let crc_expected = u32::from_le_bytes(data[pos + 12..pos + 16].try_into().unwrap());
        let flags = u32::from_le_bytes(data[pos + 16..pos + 20].try_into().unwrap());
        let body_start = pos + RECORD_HEADER_SIZE;
        let body_end = body_start + payload_len;
        if body_end > data.len() {
            return Err(pyo3::exceptions::PyValueError::new_err("truncated payload"));
        }
        let payload = &data[body_start..body_end];
        let crc_actual = crc32(payload);
        if crc_actual != crc_expected {
            return Err(pyo3::exceptions::PyValueError::new_err(format!("CRC mismatch at index {}: {} != {}", index, crc_actual, crc_expected)));
        }
        if record_id_le(payload) != rid {
            return Err(pyo3::exceptions::PyValueError::new_err(format!("record id mismatch at index {}", index)));
        }
        let d = PyDict::new_bound(py);
        d.set_item("record_id", rid)?;
        d.set_item("crc32", crc_expected)?;
        d.set_item("flags", flags)?;
        d.set_item("payload", PyBytes::new_bound(py, payload))?;
        records.append(d)?;
        pos = body_end;
        index += 1;
    }
    if record_count != index {
        return Err(pyo3::exceptions::PyValueError::new_err(format!("record_count mismatch: header {} != {} parsed", record_count, index)));
    }

    let out = PyDict::new_bound(py);
    out.set_item("header", header)?;
    out.set_item("records", records)?;
    Ok(out)
}
