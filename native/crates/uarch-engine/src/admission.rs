//! Complete admitted fixed-delay closure validation, independent of the Python caller.
use crate::{
    Delay, Job,
    carrier::{self, Result, refuse},
    hardware, wire,
};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
const PRODUCTION: &str = "sha256:3b7186f3e69d38723ec40f9a074b941934644ac57cc6f61d64865429caac07d9";
pub(crate) struct Trust {
    pub registry: String,
    pub profiles: BTreeMap<String, BTreeSet<String>>,
    pub engine: Value,
}
pub(crate) struct Validated {
    pub raw: Value,
    pub jobs: Vec<Job>,
    pub releases: Vec<(u32, u64)>,
    pub clocks: Vec<u64>,
    pub owner_ids: Vec<u64>,
    pub job_ids: Vec<String>,
}
fn require(ok: bool, code: &'static str, path: &str) -> Result<()> {
    if ok {
        Ok(())
    } else {
        Err(refuse(code, path, "installed closure condition failed"))
    }
}
pub(crate) fn identity(v: &Value, key: &str) -> Result<()> {
    let mut body = v.clone();
    body.as_object_mut()
        .ok_or_else(|| refuse("InvalidCarrier", "", "object required"))?
        .remove(key);
    require(
        v[key] == hardware::digest(&body)?,
        "ContentHashMismatch",
        key,
    )
}
fn sorted(values: Vec<Value>, code: &'static str) -> Result<()> {
    // Values are strings, integers, or pairs thereof. Never compare serialized
    // integers lexically. Callers that admit unbounded ints do not use this helper.
    fn cmp(a: &Value, b: &Value) -> std::cmp::Ordering {
        match (a, b) {
            (Value::String(a), Value::String(b)) => a.cmp(b),
            (Value::Number(a), Value::Number(b)) => a.as_u64().cmp(&b.as_u64()),
            (Value::Array(a), Value::Array(b)) => a
                .iter()
                .zip(b)
                .map(|(a, b)| cmp(a, b))
                .find(|x| !x.is_eq())
                .unwrap_or(a.len().cmp(&b.len())),
            _ => std::cmp::Ordering::Equal,
        }
    }
    require(
        values.windows(2).all(|w| cmp(&w[0], &w[1]).is_lt()),
        code,
        "",
    )
}
fn array(v: &Value) -> &Vec<Value> {
    v.as_array().expect("validated carrier array")
}
fn text(v: &Value) -> &str {
    v.as_str().expect("validated carrier string")
}
fn num(v: &Value) -> u64 {
    v.as_u64().expect("validated u64")
}
fn profile(p: &mut Value) -> Result<()> {
    for e in p["entries"].as_array_mut().expect("shape") {
        hardware::validate(&mut e["hardware_spec"])?;
        require(
            e["hardware_spec_hash"] == hardware::digest(&e["hardware_spec"])?,
            "HardwareMismatch",
            "",
        )?;
        require(
            e["freq_hz"] == hardware::frequencies(&e["hardware_spec"], &e["frequency_ratio"])?,
            "TestVariantNotAdmitted",
            "",
        )?;
        sorted(
            array(&e["allowed_job_kinds"]).clone(),
            "TestProfileMismatch",
        )?;
        require(
            !text(&e["case_id"]).contains('*'),
            "TestProfileMismatch",
            "",
        )?;
    }
    identity(p, "profile_hash")?;
    sorted(
        array(&p["entries"])
            .iter()
            .map(|e| e["case_id"].clone())
            .collect(),
        "TestProfileMismatch",
    )
}
fn point(p: &Value, owners: &[Value]) -> Result<()> {
    let g = &p["task_graph"];
    identity(g, "graph_hash")?;
    identity(p, "payload_hash")?;
    sorted(
        array(&g["jobs"]).iter().map(|j| j["id"].clone()).collect(),
        "InvalidDependency",
    )?;
    sorted(
        array(&g["dependencies"])
            .iter()
            .map(|d| serde_json::json!([d["before"], d["after"]]))
            .collect(),
        "InvalidDependency",
    )?;
    require(
        array(&g["buffers"]).is_empty()
            && array(&g["coverage"]).is_empty()
            && array(&g["routes"]).is_empty(),
        "UnsupportedCheckpointScope",
        "",
    )?;
    let ids: BTreeSet<_> = array(&g["jobs"]).iter().map(|j| text(&j["id"])).collect();
    for j in array(&g["jobs"]) {
        require(
            j["kind"] == "fixed_delay" && owners.contains(&j["owner_id"]),
            "UnsupportedCheckpointScope",
            "",
        )?;
    }
    let mut remaining: BTreeSet<_> = ids.clone();
    let mut done = BTreeSet::new();
    for d in array(&g["dependencies"]) {
        require(
            ids.contains(text(&d["before"]))
                && ids.contains(text(&d["after"]))
                && d["before"] != d["after"],
            "InvalidDependency",
            "",
        )?;
    }
    while !remaining.is_empty() {
        let ready: Vec<_> = remaining
            .iter()
            .copied()
            .filter(|id| {
                array(&g["dependencies"])
                    .iter()
                    .filter(|d| text(&d["after"]) == *id)
                    .all(|d| done.contains(text(&d["before"])))
            })
            .collect();
        require(!ready.is_empty(), "InvalidDependency", "")?;
        for id in ready {
            remaining.remove(id);
            done.insert(id);
        }
    }
    Ok(())
}
pub(crate) fn validate(input: &str, trust: &Trust) -> Result<Validated> {
    let v = wire::parse(&wire::normalize_integer_zero(input))
        .map_err(|e| refuse("InvalidJson", "", e))?;
    require(
        v["protocol"] == "uarch-engine/3",
        "UnsupportedProtocol",
        "/protocol",
    )?;
    require(
        v["workload_closure"]["scope"]["kind"] == "kernel_fixture",
        "UnsupportedCheckpointScope",
        "/workload_closure/scope",
    )?;
    let mut v = carrier::normalize(v)?;
    hardware::validate(&mut v["workload_closure"]["hardware_spec"])?;
    require(!v["profile"].is_null(), "TestProfileMismatch", "/profile")?;
    profile(&mut v["profile"])?;
    let b = &v["workload_closure"];
    let p = &v["mapped_point"];
    let a = &v["admission"];
    let owner_values = array(&b["scope"]["owner_ids"]);
    sorted(owner_values.clone(), "InvalidResource")?;
    sorted(
        array(&b["points"])
            .iter()
            .map(|p| p["point_id"].clone())
            .collect(),
        "MissingCoverage",
    )?;
    for item in array(&b["points"]) {
        point(item, owner_values)?;
    }
    point(p, owner_values)?;
    identity(&b["assumptions"], "assumptions_hash")?;
    identity(&v["assumptions"], "assumptions_hash")?;
    identity(b, "bundle_hash")?;
    identity(&v["registry"], "registry_hash")?;
    sorted(
        array(&v["registry"]["test_only_specs"])
            .iter()
            .map(|e| e["hardware_spec_hash"].clone())
            .collect(),
        "TestProfileMismatch",
    )?;
    require(
        !array(&v["registry"]["test_only_specs"])
            .iter()
            .any(|e| e["hardware_spec_hash"] == PRODUCTION),
        "TestProfileMismatch",
        "",
    )?;
    require(
        b["hardware_spec_hash"] == hardware::digest(&b["hardware_spec"])?,
        "HardwareMismatch",
        "",
    )?;
    require(
        b["assumptions_hash"] == b["assumptions"]["assumptions_hash"],
        "ContentHashMismatch",
        "",
    )?;
    require(
        v["bundle_hash"] == b["bundle_hash"]
            && v["point_hash"] == p["payload_hash"]
            && array(&b["points"]).contains(p)
            && v["assumptions_hash"] == b["assumptions_hash"]
            && v["assumptions"] == b["assumptions"],
        "ContentHashMismatch",
        "",
    )?;
    require(
        v["hardware_spec_hash"] == b["hardware_spec_hash"]
            && v["hardware"] == hardware::projection(&b["hardware_spec"])?,
        "HardwareMismatch",
        "",
    )?;
    require(
        v["rank"] == b["rank"] && a == &b["admission"],
        "AdmissionMismatch",
        "",
    )?;
    for k in ["frequency_ratio", "initial_state", "priming_iterations"] {
        require(v[k] == p[k], "AdmissionMismatch", k)?;
    }
    require(
        v["freq_hz"] == hardware::frequencies(&b["hardware_spec"], &p["frequency_ratio"])?,
        "UnsupportedFrequency",
        "",
    )?;
    require(
        v["state_model"] == "fixed_delay/1"
            && v["fidelity_detail"].is_null()
            && v["engine"]["model"]["name"] == "fixed-delay",
        "UnsupportedFidelity",
        "",
    )?;
    require(v["precision"].is_null(), "UnsupportedPrecision", "")?;
    require(v["request_hash"].is_null(), "UnsupportedWorkloadScope", "")?;
    require(
        a["checkpoint"] == "K2"
            && a["invocation"] == "test"
            && a["eligibility"] == "verification_only"
            && !a["case_id"].is_null()
            && !a["profile_hash"].is_null(),
        "AdmissionMismatch",
        "",
    )?;
    require(
        p["initial_state"] == "fixture_cold" && p["priming_iterations"] == 0,
        "UnsupportedInitialState",
        "",
    )?;
    sorted(
        array(&v["owners"])
            .iter()
            .map(|o| o["owner_id"].clone())
            .collect(),
        "InvalidResource",
    )?;
    require(
        array(&v["owners"])
            .iter()
            .map(|o| o["owner_id"].clone())
            .collect::<Vec<_>>()
            == *owner_values,
        "InvalidResource",
        "",
    )?;
    sorted(
        array(&v["clock_setup"])
            .iter()
            .map(|s| s["job_id"].clone())
            .collect(),
        "InvalidResource",
    )?;
    let entries: Vec<_> = array(&v["profile"]["entries"])
        .iter()
        .filter(|e| e["case_id"] == a["case_id"])
        .collect();
    require(entries.len() == 1, "TestProfileMismatch", "")?;
    let e = entries[0];
    require(
        e["clock_setup_hash"] == hardware::digest(&v["clock_setup"])?,
        "TestProfileMismatch",
        "",
    )?;
    for (left, right) in [
        (&a["checkpoint"], &e["checkpoint"]),
        (&b["scope"]["kind"], &e["scope"]),
        (&p["initial_state"], &e["initial_state"]),
        (&p["priming_iterations"], &e["priming_iterations"]),
        (&b["hardware_spec_hash"], &e["hardware_spec_hash"]),
        (&p["frequency_ratio"], &e["frequency_ratio"]),
        (&p["task_graph"]["graph_hash"], &e["graph_hash"]),
        (&p["payload_hash"], &e["point_hash"]),
        (&v["seed"], &e["seed"]),
    ] {
        require(left == right, "TestVariantNotAdmitted", "")?;
    }
    require(
        e["expected_outcome"] == "success"
            && array(&e["allowed_job_kinds"]).contains(&Value::String("fixed_delay".into())),
        "TestVariantNotAdmitted",
        "",
    )?;
    if b["hardware_spec_hash"] != PRODUCTION {
        require(
            array(&v["registry"]["test_only_specs"])
                .iter()
                .any(|e| e["hardware_spec_hash"] == b["hardware_spec_hash"]),
            "TestProfileMismatch",
            "",
        )?;
    }
    identity(&v, "job_hash")?;
    // External finite authority is checked separately from every content self-hash.
    require(
        v["registry"]["registry_hash"] == trust.registry,
        "RegistryTrustMismatch",
        "",
    )?;
    require(
        a["profile_hash"] == v["profile"]["profile_hash"]
            && trust
                .profiles
                .get(text(&a["profile_hash"]))
                .is_some_and(|ids| ids.contains(text(&a["case_id"]))),
        "TestProfileMismatch",
        "",
    )?;
    require(v["engine"] == trust.engine, "EngineIdentityMismatch", "")?;
    let owner_ids: Vec<_> = owner_values.iter().map(num).collect();
    let job_ids: Vec<String> = array(&p["task_graph"]["jobs"])
        .iter()
        .map(|j| text(&j["id"]).into())
        .collect();
    require(
        owner_ids.len() <= u32::MAX as usize && job_ids.len() <= u32::MAX as usize,
        "CapacityExceeded",
        "",
    )?;
    let clocks = vec![
        num(&v["freq_hz"]["core"]),
        num(&v["freq_hz"]["noc"]),
        num(&v["freq_hz"]["dram"]),
    ];
    let mut jobs = Vec::new();
    let mut releases = Vec::new();
    for (i, j) in array(&p["task_graph"]["jobs"]).iter().enumerate() {
        let setup = array(&v["clock_setup"])
            .iter()
            .find(|s| s["job_id"] == j["id"]);
        let duration = if let Some(s) = setup {
            require(j["duration_ps"] == 0, "UnsupportedScope", "clock_setup")?;
            releases.push((i as u32, num(&s["start_ps"])));
            Delay::Cycles {
                domain: ["core", "noc", "dram"]
                    .iter()
                    .position(|d| *d == text(&s["domain"]))
                    .expect("shape"),
                n_cycles: num(&s["n_cycles"]),
            }
        } else {
            Delay::Picoseconds(num(&j["duration_ps"]))
        };
        let dependencies = array(&p["task_graph"]["dependencies"])
            .iter()
            .filter(|d| d["after"] == j["id"])
            .map(|d| {
                job_ids
                    .binary_search(&text(&d["before"]).to_owned())
                    .expect("graph") as u32
            })
            .collect();
        jobs.push(Job {
            id: i as u32,
            owner: owner_ids
                .binary_search(&num(&j["owner_id"]))
                .expect("owner") as u32,
            duration,
            dependencies,
        });
    }
    require(
        array(&v["clock_setup"]).iter().all(|s| {
            job_ids
                .binary_search(&text(&s["job_id"]).to_owned())
                .is_ok()
        }),
        "InvalidResource",
        "",
    )?;
    Ok(Validated {
        raw: v,
        jobs,
        releases,
        clocks,
        owner_ids,
        job_ids,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    fn fixture() -> (Value, Trust) {
        let v: Value =
            serde_json::from_str(include_str!("../testdata/synthetic-kernel-job.json")).unwrap();
        let trust = Trust {
            registry: text(&v["registry"]["registry_hash"]).into(),
            profiles: BTreeMap::from([(
                text(&v["profile"]["profile_hash"]).into(),
                BTreeSet::from([text(&v["admission"]["case_id"]).into()]),
            )]),
            engine: v["engine"].clone(),
        };
        (v, trust)
    }
    #[test]
    fn validate_synthetic_carrier_without_execution() {
        let (v, t) = fixture();
        let valid = validate(&wire::canonical(&v).unwrap(), &t).unwrap();
        assert_eq!(valid.raw, v);
        assert_eq!(valid.jobs.len(), 3);
        // This only validates a DTO. It never calls Simulation or public execution.
    }
    #[test]
    fn malformed_carriers_refuse_before_execution() {
        let (v, t) = fixture();
        for (pointer, bad) in [
            ("/seed", serde_json::json!(true)),
            ("/seed", serde_json::json!(1.0)),
            ("/hardware/leaves/0/value", serde_json::json!(1.0)),
            (
                "/workload_closure/hardware_spec/tdp_w/unit",
                serde_json::json!("\u{1c}"),
            ),
            ("/freq_hz/core", serde_json::json!(0)),
            ("/owners/0/owner_id", serde_json::json!("0")),
        ] {
            let mut changed = v.clone();
            *changed.pointer_mut(pointer).unwrap() = bad;
            assert!(
                validate(&wire::canonical(&changed).unwrap(), &t).is_err(),
                "{pointer}"
            );
        }
        let mut unknown = v.clone();
        unknown["workload_closure"]["hardware_spec"]["tdp_w"]["unexpected"] = Value::Null;
        assert_eq!(
            validate(&wire::canonical(&unknown).unwrap(), &t)
                .err()
                .unwrap()
                .code,
            "InvalidCarrier"
        );
    }
    #[test]
    fn content_rehash_is_not_external_trust() {
        let (v, mut t) = fixture();
        t.registry = "sha256:wrong".into();
        assert_eq!(
            validate(&wire::canonical(&v).unwrap(), &t)
                .err()
                .unwrap()
                .code,
            "RegistryTrustMismatch"
        );
        let (v, mut t) = fixture();
        t.profiles.clear();
        assert_eq!(
            validate(&wire::canonical(&v).unwrap(), &t)
                .err()
                .unwrap()
                .code,
            "TestProfileMismatch"
        );
        let (v, mut t) = fixture();
        t.engine["implementation_hash"] = Value::String("sha256:wrong".into());
        assert_eq!(
            validate(&wire::canonical(&v).unwrap(), &t)
                .err()
                .unwrap()
                .code,
            "EngineIdentityMismatch"
        );
    }
}
