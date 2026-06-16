use pyo3::prelude::*;
use pyo3::types::PyBytes;
use sha2::{Digest, Sha256};

fn crc32_ieee(bytes: &[u8]) -> u32 {
    let mut crc: u32 = 0xFFFF_FFFF;
    for &byte in bytes {
        crc ^= byte as u32;
        for _ in 0..8 {
            let mask = 0u32.wrapping_sub(crc & 1);
            crc = (crc >> 1) ^ (0xEDB8_8320 & mask);
        }
    }
    !crc
}

fn record_id_u64_le(payload: &[u8]) -> u64 {
    let digest = Sha256::digest(payload);
    let mut id = [0u8; 8];
    id.copy_from_slice(&digest[0..8]);
    u64::from_le_bytes(id)
}

fn encode_v00j_record(kind: u32, trust: u32, payload: &[u8]) -> Vec<u8> {
    let record_id = record_id_u64_le(payload);
    let crc = crc32_ieee(payload);
    let mut out = Vec::with_capacity(24 + payload.len());
    out.extend_from_slice(&record_id.to_le_bytes());
    out.extend_from_slice(&kind.to_le_bytes());
    out.extend_from_slice(&trust.to_le_bytes());
    out.extend_from_slice(&(payload.len() as u32).to_le_bytes());
    out.extend_from_slice(&crc.to_le_bytes());
    out.extend_from_slice(payload);
    out
}

#[pyfunction]
pub fn v00j_batch_encode_records(
    py: Python<'_>,
    records: Vec<(u32, u32, Vec<u8>)>,
) -> PyResult<Vec<Py<PyBytes>>> {
    let mut out: Vec<Py<PyBytes>> = Vec::with_capacity(records.len());
    for (kind, trust, payload) in records {
        let encoded = encode_v00j_record(kind, trust, &payload);
        out.push(PyBytes::new_bound(py, &encoded).unbind());
    }
    Ok(out)
}

#[pyfunction]
pub fn v00j_batch_count_payload_bytes(records: Vec<(u32, u32, Vec<u8>)>) -> PyResult<usize> {
    let mut total: usize = 0;
    for (_, _, payload) in records {
        total += payload.len();
    }
    Ok(total)
}
