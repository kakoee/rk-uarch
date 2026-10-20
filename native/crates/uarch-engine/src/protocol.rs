//! Ordinary /4 EOF JSON transport. Versions and capabilities, no build authority.
use crate::{
    carrier::{Result, refuse},
    wire,
};
use serde_json::{Value, json};
pub const MAX_INPUT_BYTES: usize = 64 * 1024 * 1024;
pub const MAX_OUTPUT_BYTES: usize = 64 * 1024 * 1024;
pub const MAX_JOBS: usize = 100_000;
pub const MAX_OWNERS: usize = 100_000;
pub const MAX_EVENTS: usize = 1_000_000;
pub const MAX_OBSERVATIONS: usize = 2_000_000;
pub fn respond(input: &[u8]) -> Result<Vec<u8>> {
    respond_with_test_mode(input, false)
}

pub fn respond_with_test_mode(input: &[u8], test_only: bool) -> Result<Vec<u8>> {
    if input.len() > MAX_INPUT_BYTES {
        return Err(refuse("CapacityExceeded", "", "input byte limit"));
    }
    let text = std::str::from_utf8(input).map_err(|e| refuse("InvalidJson", "", e.to_string()))?;
    // Malformed input is rejected before model execution.
    let raw = wire::parse(&wire::normalize_integer_zero(text))
        .map_err(|e| refuse("InvalidJson", "", e))?;
    if raw["protocol"] != "uarch-engine/4" {
        return Err(refuse(
            "UnsupportedProtocol",
            "/protocol",
            "uarch-engine/4 required; historical formats use their historical executables",
        ));
    }
    if (raw["admission"]["invocation"] == "test") != test_only {
        return Err(refuse(
            "AdmissionMismatch",
            "/admission/invocation",
            "explicit test-only invocation must match job",
        ));
    }
    let result = crate::component::execute_ordinary(text)?;
    let bytes = wire::canonical(&result)
        .map_err(|e| refuse("InternalError", "", e))?
        .into_bytes();
    if bytes.len() > MAX_OUTPUT_BYTES {
        return Err(refuse("CapacityExceeded", "", "complete output byte limit"));
    }
    Ok(bytes)
}
pub fn error_bytes(error: &crate::carrier::Refusal) -> Vec<u8> {
    wire::canonical(&json!({"code":error.code,"message":error.message,"pointer":if error.pointer.is_empty(){Value::Null}else{Value::String(error.pointer.clone())}})).expect("finite error strings").into_bytes()
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn transport_refusals_do_not_need_any_authority() {
        for input in [b"".as_slice(), b"{} {}", b"{\"x\":0,\"x\":1}", b"\xff"] {
            assert_eq!(respond(input).unwrap_err().code, "InvalidJson");
        }
        assert_eq!(respond(b"{}").unwrap_err().code, "UnsupportedProtocol");
    }
}

#[cfg(test)]
mod ordinary_capability_tests {
    use super::*;
    fn seal(v: &mut Value, key: &str) {
        v.as_object_mut().unwrap().remove(key);
        v[key] = json!(crate::hardware::digest(v).unwrap());
    }
    #[test]
    fn checker_hardware_domain() {
        for pointer in [
            "/cores/core_type/job_overhead_cycles/value",
            "/sync/barrier_latency_cycles/value",
        ] {
            for value in [16, 32, 64] {
                let mut v =
                    wire::parse(include_str!("../tests/data/ordinary-fixture.json")).unwrap();
                *v["workload_closure"]["hardware_spec"]
                    .pointer_mut(pointer)
                    .unwrap() = json!(value as f64);
                let hash = json!(
                    crate::hardware::digest(&v["workload_closure"]["hardware_spec"]).unwrap()
                );
                v["hardware_spec_hash"] = hash.clone();
                v["workload_closure"]["hardware_spec_hash"] = hash.clone();
                v["hardware"] =
                    crate::hardware::projection(&v["workload_closure"]["hardware_spec"]).unwrap();
                seal(&mut v["workload_closure"], "bundle_hash");
                v["bundle_hash"] = v["workload_closure"]["bundle_hash"].clone();
                seal(&mut v, "job_hash");
                let result = respond_with_test_mode(wire::canonical(&v).unwrap().as_bytes(), true);
                if value == 32 {
                    assert!(result.is_ok(), "{:?}", result);
                } else {
                    assert_eq!(result.unwrap_err().code, "UnsupportedHardware");
                }
            }
        }
    }
}
