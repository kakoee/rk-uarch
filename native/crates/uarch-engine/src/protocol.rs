//! One EOF-delimited request per process. Build authority is never read from stdin.
use crate::{
    Error, Simulation, accounting, admission,
    carrier::{Result, refuse},
    wire,
};
use serde_json::{Value, json};
#[cfg(not(test))]
use std::collections::{BTreeMap, BTreeSet};
pub const MAX_INPUT_BYTES: usize = 64 * 1024 * 1024;
pub const MAX_OUTPUT_BYTES: usize = 64 * 1024 * 1024;
pub const MAX_JOBS: usize = 100_000;
pub const MAX_OWNERS: usize = 100_000;
pub const MAX_EVENTS: usize = 1_000_000;
pub const MAX_OBSERVATIONS: usize = 2_000_000;
#[cfg(not(test))]
mod generated {
    include!("../generated/identity.rs");
}
#[cfg(not(test))]
fn authority() -> Result<admission::Trust> {
    let engine: Value =
        wire::parse(generated::ENGINE_JSON).map_err(|e| refuse("InternalError", "", e))?;
    let trust: Value =
        wire::parse(generated::TRUST_JSON).map_err(|e| refuse("InternalError", "", e))?;
    let registry = trust["registry_hash"]
        .as_str()
        .ok_or_else(|| refuse("InternalError", "", "compiled registry"))?
        .to_owned();
    let mut profiles = BTreeMap::new();
    for profile in trust["profiles"]
        .as_array()
        .ok_or_else(|| refuse("InternalError", "", "compiled profiles"))?
    {
        let hash = profile["profile_hash"]
            .as_str()
            .ok_or_else(|| refuse("InternalError", "", "compiled profile"))?;
        let cases = profile["cases"]
            .as_array()
            .ok_or_else(|| refuse("InternalError", "", "compiled cases"))?
            .iter()
            .map(|c| {
                c["case_id"]
                    .as_str()
                    .map(str::to_owned)
                    .ok_or_else(|| refuse("InternalError", "", "compiled case"))
            })
            .collect::<Result<BTreeSet<_>>>()?;
        profiles.insert(hash.into(), cases);
    }
    Ok(admission::Trust {
        registry,
        profiles,
        engine,
    })
}
#[cfg(test)]
fn authority() -> Result<admission::Trust> {
    Err(refuse(
        "InternalError",
        "",
        "unit build has no public execution authority",
    ))
}
fn caps(v: &admission::Validated) -> Result<()> {
    let edges = v
        .jobs
        .iter()
        .try_fold(0usize, |n, j| n.checked_add(j.dependencies.len()))
        .ok_or_else(|| refuse("CapacityExceeded", "", "dependency count"))?;
    let events = v
        .jobs
        .len()
        .checked_mul(3)
        .and_then(|n| n.checked_add(edges))
        .and_then(|n| n.checked_add(v.releases.len()))
        .ok_or_else(|| refuse("CapacityExceeded", "", "event bound"))?;
    let observations = events
        .checked_add(
            v.jobs
                .len()
                .checked_mul(6)
                .ok_or_else(|| refuse("CapacityExceeded", "", "observation bound"))?,
        )
        .ok_or_else(|| refuse("CapacityExceeded", "", "observation bound"))?;
    if v.jobs.len() > MAX_JOBS
        || v.owner_ids.len() > MAX_OWNERS
        || events > MAX_EVENTS
        || observations > MAX_OBSERVATIONS
    {
        return Err(refuse(
            "CapacityExceeded",
            "",
            "operational job/owner/event/observation limit",
        ));
    }
    Ok(())
}
pub fn respond(input: &[u8]) -> Result<Vec<u8>> {
    if input.len() > MAX_INPUT_BYTES {
        return Err(refuse("CapacityExceeded", "", "input byte limit"));
    }
    let text = std::str::from_utf8(input).map_err(|e| refuse("InvalidJson", "", e.to_string()))?;
    // Malformed input is rejected independently of compiled admission.
    let raw = wire::parse(&wire::normalize_integer_zero(text))
        .map_err(|e| refuse("InvalidJson", "", e))?;
    if raw["protocol"] != "uarch-engine/3" {
        return Err(refuse(
            "UnsupportedProtocol",
            "/protocol",
            "uarch-engine/3 required",
        ));
    }
    let trust = authority()?;
    let v = admission::validate(text, &trust)?;
    caps(&v)?;
    let out = Simulation::with_releases(
        v.clocks.clone(),
        v.owner_ids.len(),
        v.jobs.clone(),
        v.releases.clone(),
    )
    .and_then(Simulation::run)
    .map_err(|e| match e {
        Error::TimeOverflow => refuse("TimeOverflow", "", "checked clock/service time overflow"),
        _ => refuse(
            "InternalError",
            "",
            format!("validated simulation failed: {e:?}"),
        ),
    })?;
    let result = accounting::construct(&v, &out)?;
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
