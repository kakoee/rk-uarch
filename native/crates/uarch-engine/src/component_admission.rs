//! Independent component admission. No caller prevalidation or computed delays.
use crate::{
    admission::Trust,
    carrier::{Result, refuse},
};
use serde_json::Value;
use std::collections::BTreeMap;
#[derive(Clone, Debug)]
pub(crate) struct Admitted {
    pub raw: Value,
    pub graph: Graph,
    pub hardware: Hardware,
    pub owners: BTreeMap<String, u64>,
}
#[derive(Clone, Debug)]
pub(crate) struct Graph {
    pub jobs: Vec<Task>,
    pub buffers: Vec<Buffer>,
    pub routes: Vec<Route>,
    pub dependencies: Vec<(usize, usize)>,
}
#[derive(Clone, Debug)]
pub(crate) struct Task {
    pub id: String,
    pub op_id: Option<String>,
    pub owner: u64,
    pub kind: TaskKind,
    pub raw: Value,
}
#[derive(Clone, Debug)]
pub(crate) enum TaskKind {
    Compute {
        core: u64,
        m: u64,
        k: u64,
        n: u64,
    },
    Dma {
        engine: u64,
        core: u64,
        write: bool,
        source: String,
        destination: String,
        fragments: Vec<Fragment>,
    },
    Unicast {
        source: String,
        destination: String,
        payload: u64,
        route: usize,
    },
    Barrier,
}
#[derive(Clone, Debug)]
pub(crate) struct Fragment {
    pub id: String,
    pub payload: u64,
    pub channel: u64,
    pub route: usize,
}
#[derive(Clone, Debug)]
pub(crate) struct Route {
    pub hops: u64,
    pub owner: u64,
}
#[derive(Clone, Debug)]
pub(crate) struct Buffer {
    pub id: String,
    pub space: String,
    pub owner: u64,
    pub offset: u64,
    pub size: u64,
    pub producer: Option<usize>,
    pub consumers: Vec<usize>,
    pub persistent: bool,
}
#[derive(Clone, Debug)]
pub(crate) struct Hardware {
    pub freq: [u64; 3],
    pub operand_rate: u64,
    pub port_rate: u64,
    pub overhead: u64,
    pub wave_fill_drain: u64,
    pub hop_cycles: u64,
    pub dram_latency: u64,
    pub barrier_cycles: u64,
    pub credit_limit: u64,
    pub engines_per_core: u64,
    pub channel_step_num: u128,
    pub channel_step_den: u128,
}
fn require(ok: bool, code: &'static str, detail: &str) -> Result<()> {
    if ok {
        Ok(())
    } else {
        Err(refuse(code, "", detail))
    }
}
fn arr(v: &Value) -> &Vec<Value> {
    v.as_array().expect("component shape checked")
}
fn txt(v: &Value) -> &str {
    v.as_str().expect("component shape checked")
}
fn num(v: &Value) -> u64 {
    v.as_u64().expect("component bounded integer checked")
}
fn integer(v: &Value) -> Result<u64> {
    let (n, d) = crate::hardware::ratio(&v["value"])?;
    require(
        d == 1,
        "UnsupportedHardware",
        "integral hardware field required",
    )?;
    u64::try_from(n).map_err(|_| refuse("CapacityExceeded", "", "hardware integer overflow"))
}
fn add(a: u64, b: u64) -> Result<u64> {
    a.checked_add(b)
        .ok_or_else(|| refuse("CapacityExceeded", "", "integer sum overflow"))
}
fn mul(a: u64, b: u64) -> Result<u64> {
    a.checked_mul(b)
        .ok_or_else(|| refuse("CapacityExceeded", "", "integer product overflow"))
}
fn sorted(values: Vec<String>, code: &'static str) -> Result<()> {
    require(
        values.windows(2).all(|w| w[0] < w[1]),
        code,
        "sorted unique inventory",
    )
}
fn keys(v: &Value) -> std::collections::BTreeSet<&str> {
    v.as_object()
        .expect("shape map")
        .keys()
        .map(String::as_str)
        .collect()
}
fn strings(v: &Value) -> std::collections::BTreeSet<&str> {
    arr(v).iter().map(txt).collect()
}
fn identity(v: &Value, key: &str) -> Result<()> {
    crate::admission::identity(v, key)
}
fn graph_laws(p: &Value) -> Result<BTreeMap<String, std::collections::BTreeSet<String>>> {
    let g = &p["task_graph"];
    identity(g, "graph_hash")?;
    identity(p, "payload_hash")?;
    for (section, key, code) in [
        ("jobs", "id", "InvalidDependency"),
        ("buffers", "id", "InvalidResource"),
        ("routes", "id", "InvalidRoute"),
        ("coverage", "job_id", "InvalidCoverage"),
    ] {
        sorted(
            arr(&g[section])
                .iter()
                .map(|x| txt(&x[key]).into())
                .collect(),
            code,
        )?;
    }
    let ids: std::collections::BTreeSet<_> = arr(&g["jobs"])
        .iter()
        .map(|j| txt(&j["id"]).to_owned())
        .collect();
    let mut incoming: BTreeMap<String, std::collections::BTreeSet<String>> = ids
        .iter()
        .map(|k| (k.clone(), Default::default()))
        .collect();
    let mut previous: Option<(&str, &str)> = None;
    for d in arr(&g["dependencies"]) {
        let pair = (txt(&d["before"]), txt(&d["after"]));
        require(
            previous.is_none_or(|p| p < pair),
            "InvalidDependency",
            "dependency order",
        )?;
        previous = Some(pair);
        require(
            pair.0 != pair.1 && ids.contains(pair.0) && ids.contains(pair.1),
            "InvalidDependency",
            "dependency endpoints",
        )?;
        incoming
            .get_mut(pair.1)
            .expect("checked")
            .insert(pair.0.into());
    }
    let mut done = std::collections::BTreeSet::new();
    let mut ancestors = incoming.clone();
    while done.len() < ids.len() {
        let ready: Vec<_> = ids
            .iter()
            .filter(|k| !done.contains(*k) && incoming[*k].is_subset(&done))
            .cloned()
            .collect();
        require(!ready.is_empty(), "InvalidDependency", "cycle")?;
        for id in ready {
            let mut all = incoming[&id].clone();
            for parent in &incoming[&id] {
                all.extend(ancestors[parent].clone());
            }
            ancestors.insert(id.clone(), all);
            done.insert(id);
        }
    }
    let computes: BTreeMap<_, _> = arr(&g["jobs"])
        .iter()
        .filter(|j| j["kind"] == "compute")
        .map(|j| (txt(&j["id"]), j))
        .collect();
    require(
        computes
            .keys()
            .copied()
            .collect::<std::collections::BTreeSet<_>>()
            == arr(&g["coverage"])
                .iter()
                .map(|c| txt(&c["job_id"]))
                .collect(),
        "InvalidCoverage",
        "compute inventory",
    )?;
    for c in arr(&g["coverage"]) {
        let j = computes[txt(&c["job_id"])];
        for key in [
            "op_id",
            "group_id",
            "repeat_index",
            "tile_origin",
            "tile_extents",
        ] {
            require(c[key] == j[key], "InvalidCoverage", key)?;
        }
    }
    for j in arr(&g["jobs"]) {
        if j["kind"] == "barrier" {
            sorted(
                arr(&j["participant_job_ids"])
                    .iter()
                    .map(|x| txt(x).into())
                    .collect(),
                "InvalidDependency",
            )?;
            require(
                strings(&j["participant_job_ids"])
                    == incoming[txt(&j["id"])].iter().map(String::as_str).collect(),
                "InvalidDependency",
                "barrier participants",
            )?;
        }
    }
    Ok(ancestors)
}
fn owner_map(spec: &Value, g: &Value) -> Result<BTreeMap<String, u64>> {
    let rows = integer(&spec["cores"]["grid"]["rows"])?;
    let cols = integer(&spec["cores"]["grid"]["cols"])?;
    let count = mul(rows, cols)?;
    let engines = integer(&spec["cores"]["core_type"]["dma"]["engines"])?;
    let channels = integer(&spec["memory"]["dram"]["channels"])?;
    require(
        count > 0
            && count <= 10_000
            && engines > 0
            && mul(count, engines)? <= 100_000
            && channels <= 100_000,
        "CapacityExceeded",
        "owner bound",
    )?;
    let mut names = Vec::new();
    for kind in ["matrix", "vector", "sram"] {
        for c in 0..count {
            names.push(format!("{kind}:{c}"));
        }
    }
    for c in 0..count {
        for e in 0..engines {
            names.push(format!("dma:{c}:{e}"));
        }
    }
    for c in 0..count {
        names.push(format!("dma_port:{c}"));
    }
    for c in 0..channels {
        names.push(format!("channel:{c}"));
    }
    for n in 0..arr(&spec["nocs"]).len() {
        for r in 0..rows {
            for c in 0..cols {
                names.push(format!("router:{n}:{r}:{c}"));
            }
        }
    }
    for n in 0..arr(&spec["nocs"]).len() {
        for a in 0..count {
            let mut neighbors = Vec::new();
            if a >= cols {
                neighbors.push(a - cols);
            }
            if a % cols > 0 {
                neighbors.push(a - 1);
            }
            if a % cols + 1 < cols {
                neighbors.push(a + 1);
            }
            if a + cols < count {
                neighbors.push(a + cols);
            }
            neighbors.sort();
            for z in neighbors {
                names.push(format!("link:{n}:{a}:{z}"));
            }
        }
    }
    for j in arr(&g["jobs"]) {
        if j["kind"] == "barrier" {
            names.push(format!("barrier:{}", txt(&j["id"])));
        }
    }
    require(
        names.len() <= crate::protocol::MAX_OWNERS,
        "CapacityExceeded",
        "owner inventory",
    )?;
    Ok(names
        .into_iter()
        .enumerate()
        .map(|(i, k)| (k, i as u64))
        .collect())
}
fn profile(v: &mut Value) -> Result<()> {
    for e in v["entries"].as_array_mut().expect("profile shape") {
        crate::hardware::validate(&mut e["hardware_spec"])?;
    }
    identity(v, "profile_hash")?;
    sorted(
        arr(&v["entries"])
            .iter()
            .map(|e| txt(&e["case_id"]).into())
            .collect(),
        "TestProfileMismatch",
    )?;
    let two = v["format"] == "uarch-native-test-profile/2";
    for e in arr(&v["entries"]) {
        require(
            two == e.get("mapping_policy").is_some()
                && (!two
                    || (e["checkpoint"] == "B"
                        && (e["scope"] == "component" || e["scope"] == "transport_fixture"))),
            "TestProfileMismatch",
            "profile policy format",
        )?;
        require(
            e["hardware_spec_hash"] == crate::hardware::digest(&e["hardware_spec"])?,
            "HardwareMismatch",
            "profile hardware hash",
        )?;
        require(
            e["freq_hz"]
                == crate::hardware::frequencies(&e["hardware_spec"], &e["frequency_ratio"])?,
            "TestVariantNotAdmitted",
            "profile frequency",
        )?;
        sorted(
            arr(&e["allowed_job_kinds"])
                .iter()
                .map(|x| txt(x).into())
                .collect(),
            "TestProfileMismatch",
        )?;
        require(
            !txt(&e["case_id"]).contains('*'),
            "TestProfileMismatch",
            "wildcard case",
        )?;
    }
    Ok(())
}
const PRODUCTION: &str = "sha256:3b7186f3e69d38723ec40f9a074b941934644ac57cc6f61d64865429caac07d9";
pub(crate) fn validate(input: &str, trust: &Trust) -> Result<Admitted> {
    require(
        input.len() <= crate::protocol::MAX_INPUT_BYTES,
        "CapacityExceeded",
        "input byte limit",
    )?;
    let value = crate::wire::parse(&crate::wire::normalize_integer_zero(input))
        .map_err(|e| refuse("InvalidJson", "", e))?;
    require(
        value["protocol"] == "uarch-engine/3",
        "UnsupportedProtocol",
        "uarch-engine/3",
    )?;
    require(
        value["workload_closure"]["scope"]["kind"] != "prepared_model",
        "UnsupportedWorkloadScope",
        "component stage",
    )?;
    let mut v = crate::carrier::normalize_component(value)?;
    crate::hardware::validate(&mut v["workload_closure"]["hardware_spec"])?;
    if !v["profile"].is_null() {
        profile(&mut v["profile"])?;
    }
    let b = &v["workload_closure"];
    let p = &v["mapped_point"];
    let a = &v["admission"];
    sorted(
        arr(&b["points"])
            .iter()
            .map(|p| txt(&p["point_id"]).into())
            .collect(),
        "MissingCoverage",
    )?;
    let mut closures = Vec::new();
    for point in arr(&b["points"]) {
        require(
            arr(&point["task_graph"]["jobs"]).len() <= crate::protocol::MAX_JOBS,
            "CapacityExceeded",
            "job bound",
        )?;
        closures.push(graph_laws(point)?);
    }
    graph_laws(p)?;
    identity(&b["assumptions"], "assumptions_hash")?;
    identity(&v["assumptions"], "assumptions_hash")?;
    identity(b, "bundle_hash")?;
    require(
        b["hardware_spec_hash"] == crate::hardware::digest(&b["hardware_spec"])?,
        "HardwareMismatch",
        "bundle hardware",
    )?;
    require(
        b["assumptions_hash"] == b["assumptions"]["assumptions_hash"],
        "ContentHashMismatch",
        "assumptions closure",
    )?;
    require(
        b["source"].is_null(),
        "UnexpectedClosure",
        "component source",
    )?;
    let component = b["scope"]["kind"] == "component";
    if component {
        let ops = arr(&b["scope"]["ops"]);
        sorted(
            ops.iter().map(|x| txt(&x["id"]).into()).collect(),
            "InvalidCoverage",
        )?;
        require(
            b["scope"]["op_ids"] == Value::Array(ops.iter().map(|x| x["id"].clone()).collect()),
            "InvalidCoverage",
            "scope operators",
        )?;
        for point in arr(&b["points"]) {
            require(
                point["identity"]["kind"] == "component"
                    && point["identity"]["op_ids"] == b["scope"]["op_ids"],
                "InvalidCoverage",
                "point operator identity",
            )?;
        }
        for op in ops {
            require(
                keys(&op["operand_access"]) == std::collections::BTreeSet::from(["X", "W", "Y"]),
                "InvalidCoverage",
                "operand access",
            )?;
        }
    }
    identity(&v["registry"], "registry_hash")?;
    sorted(
        arr(&v["registry"]["test_only_specs"])
            .iter()
            .map(|e| txt(&e["hardware_spec_hash"]).into())
            .collect(),
        "TestProfileMismatch",
    )?;
    require(
        !arr(&v["registry"]["test_only_specs"])
            .iter()
            .any(|e| e["hardware_spec_hash"] == PRODUCTION),
        "TestProfileMismatch",
        "baseline registered as test-only",
    )?;
    require(
        v["bundle_hash"] == b["bundle_hash"]
            && v["point_hash"] == p["payload_hash"]
            && arr(&b["points"]).contains(p)
            && v["assumptions_hash"] == b["assumptions_hash"]
            && v["assumptions"] == b["assumptions"],
        "ContentHashMismatch",
        "full point/closure join",
    )?;
    require(
        v["hardware_spec_hash"] == b["hardware_spec_hash"]
            && v["hardware"] == crate::hardware::projection(&b["hardware_spec"])?,
        "HardwareMismatch",
        "resolved hardware",
    )?;
    require(
        v["rank"] == b["rank"] && a == &b["admission"],
        "AdmissionMismatch",
        "rank/admission join",
    )?;
    for k in ["frequency_ratio", "initial_state", "priming_iterations"] {
        require(v[k] == p[k], "AdmissionMismatch", k)?;
    }
    require(
        v["freq_hz"] == crate::hardware::frequencies(&b["hardware_spec"], &p["frequency_ratio"])?,
        "UnsupportedFrequency",
        "frequency projection",
    )?;
    require(
        v["state_model"] == "resource_intervals/1"
            && v["engine"]["model"]["name"] == "native-intervals"
            && v["fidelity_detail"]
                == serde_json::json!({"compute":1,"noc":0,"dram":0,"sync":"exact","layer_reuse":false}),
        "UnsupportedFidelity",
        "component model",
    )?;
    require(
        v["precision"] == "bf16",
        "UnsupportedPrecision",
        "component precision",
    )?;
    require(
        v["request_hash"].is_null(),
        "UnsupportedWorkloadScope",
        "no product request",
    )?;
    require(
        arr(&v["clock_setup"]).is_empty(),
        "TestOnlyScope",
        "component clock setup",
    )?;
    identity(&v, "job_hash")?;
    require(
        v["registry"]["registry_hash"] == trust.registry,
        "RegistryTrustMismatch",
        "external registry",
    )?;
    require(
        v["engine"] == trust.engine,
        "EngineIdentityMismatch",
        "external engine",
    )?;
    require(
        a["checkpoint"] == "B",
        "UnsupportedCheckpointScope",
        "component checkpoint",
    )?;
    let test = a["invocation"] == "test";
    require(
        (!a["profile_hash"].is_null()) == test && (!a["case_id"].is_null()) == test,
        "TestProfileMismatch",
        "invocation/profile binding",
    )?;
    require(
        a["eligibility"]
            == if test {
                "verification_only"
            } else {
                "component_only"
            },
        "AdmissionMismatch",
        "eligibility",
    )?;
    if test {
        require(
            !v["profile"].is_null(),
            "TestProfileMismatch",
            "profile required",
        )?;
        require(
            a["profile_hash"] == v["profile"]["profile_hash"]
                && trust
                    .profiles
                    .get(txt(&a["profile_hash"]))
                    .is_some_and(|ids| ids.contains(txt(&a["case_id"]))),
            "TestProfileMismatch",
            "external profile/case",
        )?;
        let e = arr(&v["profile"]["entries"])
            .iter()
            .find(|e| e["case_id"] == a["case_id"])
            .ok_or_else(|| refuse("TestProfileMismatch", "", "profile case absent"))?;
        if e.get("mapping_policy").is_some() {
            require(
                e["mapping_policy"] == b["mapping_policy"],
                "TestVariantNotAdmitted",
                "profile mapping policy",
            )?;
        }
        require(
            e["clock_setup_hash"] == crate::hardware::digest(&v["clock_setup"])?,
            "TestProfileMismatch",
            "clock setup",
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
            require(
                left == right,
                "TestVariantNotAdmitted",
                "profile entry join",
            )?;
        }
        require(
            e["expected_outcome"] == "success"
                && arr(&p["task_graph"]["jobs"])
                    .iter()
                    .all(|j| arr(&e["allowed_job_kinds"]).contains(&j["kind"])),
            "TestVariantNotAdmitted",
            "negative profile is not admission",
        )?;
        if b["hardware_spec_hash"] != PRODUCTION {
            require(
                arr(&v["registry"]["test_only_specs"])
                    .iter()
                    .any(|e| e["hardware_spec_hash"] == b["hardware_spec_hash"]),
                "TestProfileMismatch",
                "unregistered variant",
            )?;
        }
    } else {
        require(
            !arr(&v["registry"]["test_only_specs"])
                .iter()
                .any(|e| e["hardware_spec_hash"] == b["hardware_spec_hash"]),
            "TestOnlyHardware",
            "test hardware",
        )?;
        require(
            component,
            "UnsupportedCheckpointScope",
            "production component only",
        )?;
        require(
            b["hardware_spec_hash"] == PRODUCTION,
            "UnsupportedHardware",
            "production hardware",
        )?;
    }
    let owners = owner_map(&b["hardware_spec"], &p["task_graph"])?;
    let mut declared = arr(&v["owners"]).clone();
    let mut expected: Vec<_> = owners
        .iter()
        .map(|(resource, id)| serde_json::json!({"owner_id":id,"resource":resource}))
        .collect();
    expected.sort_by_key(|x| num(&x["owner_id"]));
    require(
        declared == expected,
        "InvalidResource",
        "canonical owner inventory",
    )?;
    declared.clear();
    for (point, ancestors) in arr(&b["points"]).iter().zip(&closures) {
        require(
            point["priming_iterations"] == 0
                && (point["initial_state"] == "cold"
                    || (test && point["initial_state"] == "fixture_resident")),
            "UnsupportedInitialState",
            "component initial state",
        )?;
        if !test {
            require(
                point["frequency_ratio"].as_f64() == Some(1.0)
                    && crate::hardware::frequencies(
                        &b["hardware_spec"],
                        &point["frequency_ratio"],
                    )? == serde_json::json!({"core":1000000000,"noc":1000000000,"dram":1000000000}),
                "UnsupportedFrequency",
                "production clocks",
            )?;
        }
        resources(b, point, ancestors)?;
    }
    let hardware = hardware_model(&v)?;
    let graph = typed_graph(b, p, &owners, &hardware)?;
    Ok(Admitted {
        raw: v,
        graph,
        hardware,
        owners,
    })
}
fn resources(
    b: &Value,
    p: &Value,
    ancestors: &BTreeMap<String, std::collections::BTreeSet<String>>,
) -> Result<()> {
    let g = &p["task_graph"];
    let spec = &b["hardware_spec"];
    let core = &spec["cores"]["core_type"];
    let rows = integer(&spec["cores"]["grid"]["rows"])?;
    let cols = integer(&spec["cores"]["grid"]["cols"])?;
    let ncores = mul(rows, cols)?;
    let sram = integer(&core["sram"]["bytes"])?;
    let banks = integer(&core["sram"]["banks"])?;
    require(
        banks > 0 && sram >= banks,
        "UnsupportedHardware",
        "SRAM bank geometry",
    )?;
    let bank_size = sram / banks;
    let buffers: BTreeMap<_, _> = arr(&g["buffers"])
        .iter()
        .map(|x| (txt(&x["id"]), x))
        .collect();
    let jobs: BTreeMap<_, _> = arr(&g["jobs"]).iter().map(|x| (txt(&x["id"]), x)).collect();
    let routes: BTreeMap<_, _> = arr(&g["routes"])
        .iter()
        .map(|x| (txt(&x["id"]), x))
        .collect();
    require(
        jobs.values().all(|j| j["kind"] != "fixed_delay"),
        "TestOnlyScope",
        "fixed delay inside component",
    )?;
    for buf in arr(&g["buffers"]) {
        let id = txt(&buf["id"]);
        require(
            num(&buf["alignment_bytes"]) == 256 && num(&buf["offset_bytes"]).is_multiple_of(256),
            "InvalidResource",
            id,
        )?;
        require(
            buf["producer_id"].is_null() || jobs.contains_key(txt(&buf["producer_id"])),
            "InvalidDependency",
            "producer absent",
        )?;
        require(
            strings(&buf["final_consumer_ids"])
                .iter()
                .all(|j| jobs.contains_key(*j)),
            "InvalidDependency",
            "consumer absent",
        )?;
        let capacity = if buf["space"] == "hbm" {
            require(
                buf["core_id"].is_null() && buf["bank"].is_null(),
                "InvalidResource",
                "HBM owner",
            )?;
            integer(&spec["memory"]["dram"]["capacity_bytes"])?
        } else {
            require(
                buf["core_id"].as_u64().is_some_and(|c| c < ncores),
                "InvalidResource",
                id,
            )?;
            if buf["space"] == "sram" {
                sram
            } else {
                integer(&core["matrix_engine"]["accumulator_bytes"])?
            }
        };
        require(
            (num(&buf["offset_bytes"]) as u128) + (num(&buf["size_bytes"]) as u128)
                <= capacity as u128,
            if buf["space"] == "sram" {
                "SramCapacityExceeded"
            } else {
                "CapacityExceeded"
            },
            id,
        )?;
        if buf["space"] == "sram" {
            require(
                buf["bank"].as_u64() == Some(num(&buf["offset_bytes"]) / bank_size),
                "InvalidBank",
                id,
            )?;
            require(
                p["initial_state"] != "cold" || buf["initial_residency"] == "uninitialized",
                "UnsupportedInitialState",
                "cold SRAM preload",
            )?;
        }
    }
    let version = txt(&b["mapping_policy"]["version"]);
    for buf in arr(&g["buffers"]) {
        if buf["space"] != "accumulator" {
            continue;
        }
        if version == "1" {
            require(
                arr(&buf["final_consumer_ids"]).is_empty(),
                "UnsupportedMapping",
                "transient accumulator policy",
            )?;
        }
        if version == "2" && !buf["producer_id"].is_null() {
            require(
                b["scope"]["kind"] == "component",
                "UnsupportedMapping",
                "transient accumulator scope",
            )?;
            let producer = jobs[txt(&buf["producer_id"])];
            require(
                producer["kind"] == "compute" && producer["accumulator_buffer_id"] == buf["id"],
                "InvalidDependency",
                "accumulator producer must use this buffer",
            )?;
            require(
                producer["core_id"] == buf["core_id"],
                "InvalidResource",
                "accumulator owner",
            )?;
            require(
                buf["initial_residency"] == "uninitialized",
                "InvalidDependency",
                "transient accumulator preload",
            )?;
        }
    }
    let mut readers: BTreeMap<&str, std::collections::BTreeSet<&str>> =
        buffers.keys().map(|k| (*k, Default::default())).collect();
    for j in arr(&g["jobs"]) {
        let id = txt(&j["id"]);
        if j["kind"] == "compute" {
            let acc = buffers
                .get(txt(&j["accumulator_buffer_id"]))
                .ok_or_else(|| refuse("InvalidResource", "", "missing accumulator"))?;
            if version == "2" && !acc["producer_id"].is_null() {
                require(
                    acc["producer_id"] == j["id"]
                        || ancestors[id].contains(txt(&acc["producer_id"])),
                    "InvalidDependency",
                    "accumulator use before production",
                )?;
                readers.get_mut(txt(&acc["id"])).expect("buffer").insert(id);
            }
            for name in ["X", "W"] {
                let key = j["operand_buffers"][name]
                    .as_str()
                    .ok_or_else(|| refuse("InvalidResource", "", "missing operand buffer"))?;
                readers
                    .get_mut(key)
                    .ok_or_else(|| refuse("InvalidResource", "", "unknown operand buffer"))?
                    .insert(id);
            }
        } else if j["kind"] == "dma" || j["kind"] == "noc_transfer" {
            readers
                .get_mut(txt(&j["source"]["buffer_id"]))
                .ok_or_else(|| refuse("InvalidResource", "", "unknown source buffer"))?
                .insert(id);
        }
    }
    for (id, buf) in &buffers {
        let terminal: std::collections::BTreeSet<_> = readers[id]
            .iter()
            .copied()
            .filter(|j| !readers[id].iter().any(|k| ancestors[*k].contains(*j)))
            .collect();
        require(
            strings(&buf["final_consumer_ids"]) == terminal,
            "InvalidDependency",
            &format!("final consumers {id}"),
        )?;
    }
    let ends_before = |x: &Value, y: &Value| -> bool {
        !arr(&x["final_consumer_ids"]).is_empty()
            && y["producer_id"].as_str().is_some_and(|producer| {
                arr(&x["final_consumer_ids"])
                    .iter()
                    .all(|j| ancestors[producer].contains(txt(j)))
            })
    };
    for (i, x) in arr(&g["buffers"]).iter().enumerate() {
        for y in &arr(&g["buffers"])[i + 1..] {
            if x["space"] != y["space"] || x["core_id"] != y["core_id"] {
                continue;
            }
            let overlap = (num(&x["offset_bytes"]) as u128)
                < num(&y["offset_bytes"]) as u128 + num(&y["size_bytes"]) as u128
                && (num(&y["offset_bytes"]) as u128)
                    < num(&x["offset_bytes"]) as u128 + num(&x["size_bytes"]) as u128;
            if overlap {
                require(
                    ends_before(x, y) || ends_before(y, x),
                    "LiveBufferAlias",
                    &format!("{}/{}", txt(&x["id"]), txt(&y["id"])),
                )?;
            }
        }
    }
    for route in arr(&g["routes"]) {
        require(
            route["noc_index"] == 0
                && num(&route["source_core_id"]) < ncores
                && num(&route["destination_core_id"]) < ncores,
            "InvalidResource",
            "route endpoints",
        )?;
        let mut current = num(&route["source_core_id"]);
        let end = num(&route["destination_core_id"]);
        let mut expected = vec![Value::from(current)];
        while current % cols != end % cols {
            if current % cols < end % cols {
                current += 1;
            } else {
                current -= 1;
            }
            expected.push(Value::from(current));
        }
        while current / cols != end / cols {
            if current < end {
                current += cols;
            } else {
                current -= cols;
            }
            expected.push(Value::from(current));
        }
        require(
            expected == *arr(&route["core_ids"]),
            "InvalidRoute",
            txt(&route["id"]),
        )?;
    }
    let mut ops = BTreeMap::new();
    if b["scope"]["kind"] == "component" {
        require(
            b["rank"]["tp"] == 1
                && b["rank"]["rank_index"] == 0
                && b["rank"]["equivalent_ranks"] == serde_json::json!([0]),
            "UnsupportedRankScope",
            "TP1/rank0",
        )?;
        require(
            b["mapping_policy"]["name"] == "ws-rowsplit"
                && matches!(version, "1" | "2")
                && b["mapping_policy"]["buffer_depth"] == 2,
            "UnsupportedMapping",
            "ws-rowsplit policy",
        )?;
        ops = arr(&b["scope"]["ops"])
            .iter()
            .map(|op| (txt(&op["id"]), op))
            .collect();
        for (id, op) in &ops {
            require(
                op["spec"]["operator"] == "q_projection",
                "UnsupportedOperator",
                id,
            )?;
            require(
                op["spec"]["operands"]
                    .as_object()
                    .expect("shape")
                    .values()
                    .all(|x| x["dtype"] == "bf16"),
                "UnsupportedPrecision",
                "operand dtype",
            )?;
            require(
                op["work_repeat"] == 1
                    && op["weight_copies"] == 1
                    && arr(&op["replication"]).is_empty()
                    && op["fusion"] == "none"
                    && op["kv_access"].is_null()
                    && op["embedding_local_tokens"].is_null(),
                "UnsupportedCapability",
                "component operator capability",
            )?;
            require(
                arr(&op["padding"]).is_empty(),
                "UnsupportedShape",
                "padding",
            )?;
            require(
                op["spec"]["operands"]
                    .as_object()
                    .expect("shape")
                    .values()
                    .all(|x| x["layout"] == "contiguous" && x["block_size_tokens"].is_null()),
                "UnsupportedCapability",
                "operand layout",
            )?;
            require(
                keys(&op["spec"]["operands"]) == std::collections::BTreeSet::from(["X", "W", "Y"])
                    && op["spec"]["reduction_axes"] == serde_json::json!(["K"]),
                "InvalidPreparedGraph",
                "operands/reduction axes",
            )?;
            for (name, axes, access) in [
                ("X", serde_json::json!(["M", "K"]), "read"),
                ("W", serde_json::json!(["K", "N"]), "read"),
                ("Y", serde_json::json!(["M", "N"]), "write"),
            ] {
                require(
                    op["spec"]["operands"][name]["dimensions"] == axes
                        && op["operand_access"][name] == access,
                    "InvalidPreparedGraph",
                    "operand axes/access",
                )?;
            }
            let d = &op["spec"]["dimensions"];
            let dim = |key: &str, max: u64| d[key].as_u64().is_some_and(|x| x >= 1 && x <= max);
            require(
                dim("M", 1024) && dim("K", 256) && dim("N", 256),
                "UnsupportedShape",
                "component dimensions",
            )?;
            require(
                arr(&op["depends_on"])
                    .iter()
                    .all(|x| ops.contains_key(txt(x)) && txt(x) != *id),
                "InvalidDependency",
                "operator dependencies",
            )?;
            let mut tiles: Vec<_> = jobs
                .values()
                .filter(|j| j["kind"] == "compute" && j["op_id"] == *id)
                .collect();
            tiles.sort_by_key(|j| num(&j["tile_origin"]["M"]));
            let mut cursor = 0;
            for tile in tiles {
                require(
                    tile["tile_origin"] == serde_json::json!({"M":cursor,"K":0,"N":0})
                        && tile["tile_extents"]["K"] == d["K"]
                        && tile["tile_extents"]["N"] == d["N"]
                        && num(&tile["tile_extents"]["M"]) <= 256,
                    "InvalidCoverage",
                    "tile extent/origin",
                )?;
                cursor = add(cursor, num(&tile["tile_extents"]["M"]))?;
            }
            require(cursor == num(&d["M"]), "InvalidCoverage", id)?;
        }
    } else {
        require(
            arr(&g["coverage"]).is_empty() && jobs.values().all(|j| j["kind"] != "compute"),
            "UnsupportedCheckpointScope",
            "transport compute",
        )?;
    }
    for (id, op) in &ops {
        let own: Vec<_> = jobs.values().filter(|j| j["op_id"] == *id).collect();
        let roots: Vec<_> = own
            .iter()
            .filter(|j| {
                !own.iter()
                    .any(|k| ancestors[txt(&j["id"])].contains(txt(&k["id"])))
            })
            .collect();
        for dep in arr(&op["depends_on"]) {
            let previous: Vec<_> = jobs
                .values()
                .filter(|j| &j["op_id"] == dep)
                .map(|j| txt(&j["id"]))
                .collect();
            require(
                !previous.is_empty()
                    && roots.iter().all(|j| {
                        previous
                            .iter()
                            .all(|k| ancestors[txt(&j["id"])].contains(*k))
                    }),
                "InvalidDependency",
                "operator dependency closure",
            )?;
        }
    }
    let mut request_ids = std::collections::BTreeSet::new();
    for j in arr(&g["jobs"]) {
        let id = txt(&j["id"]);
        if j["kind"] == "compute" {
            require(
                num(&j["core_id"]) < ncores,
                "InvalidResource",
                "compute core",
            )?;
            require(
                ops.contains_key(txt(&j["op_id"]))
                    && j["group_id"].is_null()
                    && j["repeat_index"] == 0,
                "InvalidCoverage",
                "compute operator",
            )?;
            require(
                j["engine"] == "matrix" && j["dataflow"] == "weight_stationary",
                "UnsupportedMapping",
                "compute mapping",
            )?;
            require(
                j["operand_dtypes"] == serde_json::json!({"X":"bf16","W":"bf16","Y":"bf16"}),
                "UnsupportedPrecision",
                "tile dtype",
            )?;
            require(
                keys(&j["operand_buffers"]) == std::collections::BTreeSet::from(["X", "W", "Y"]),
                "InvalidCoverage",
                "tile operands",
            )?;
            let (m, k, n) = (
                num(&j["tile_extents"]["M"]),
                num(&j["tile_extents"]["K"]),
                num(&j["tile_extents"]["N"]),
            );
            require(
                j["physical_extents"] == serde_json::json!({"M":m,"K":256,"N":256}),
                "UnsupportedShape",
                "physical extent",
            )?;
            let acc = buffers[txt(&j["accumulator_buffer_id"])];
            require(
                acc["space"] == "accumulator"
                    && acc["core_id"] == j["core_id"]
                    && num(&acc["size_bytes"]) == mul(4, mul(m, n)?)?,
                "CapacityExceeded",
                "accumulator footprint",
            )?;
            let sizes = BTreeMap::from([
                ("X", mul(2, mul(m, k)?)?),
                ("W", mul(2, mul(k, n)?)?),
                ("Y", mul(2, mul(m, n)?)?),
            ]);
            require(
                add(sizes["X"], sizes["W"])?
                    <= integer(&core["matrix_engine"]["operand_buffer_bytes"])?,
                "CapacityExceeded",
                "operand buffer",
            )?;
            require(
                j["operand_buffers"]
                    .as_object()
                    .expect("shape")
                    .values()
                    .all(|v| buffers.contains_key(txt(v))),
                "InvalidResource",
                "operand buffer absent",
            )?;
            let slots: std::collections::BTreeSet<_> = j["operand_buffers"]
                .as_object()
                .expect("shape")
                .values()
                .map(|v| buffers[txt(v)]["slot_index"].as_u64())
                .collect();
            require(
                slots.len() == 1 && !slots.contains(&None),
                "InvalidResource",
                "one explicit input/output slot",
            )?;
            let slot = slots.first().copied().flatten().expect("checked slot");
            require(
                buffers.values().any(|buf| {
                    buf["space"] == "sram"
                        && buf["core_id"] == j["core_id"]
                        && buf["slot_index"] == 1 - slot
                        && buf["operand"].is_null()
                        && num(&buf["size_bytes"]) >= sizes.values().sum()
                }),
                "CapacityExceeded",
                "second slot reservation missing",
            )?;
            for (name, size) in sizes {
                let buf = buffers[txt(&j["operand_buffers"][name])];
                require(
                    buf["space"] == "sram"
                        && buf["core_id"] == j["core_id"]
                        && num(&buf["size_bytes"]) == size
                        && buf["operand"] == name
                        && buf["op_id"] == j["op_id"],
                    "InvalidCoverage",
                    "operand buffer footprint",
                )?;
                if name == "Y" {
                    require(
                        buf["producer_id"] == j["id"],
                        "InvalidDependency",
                        "output producer",
                    )?;
                } else {
                    require(
                        buf["initial_residency"] == "preloaded"
                            || buf["producer_id"]
                                .as_str()
                                .is_some_and(|pid| ancestors[id].contains(pid)),
                        "InvalidDependency",
                        "uninitialized operand",
                    )?;
                }
            }
        }
        if j["kind"] == "dma" || j["kind"] == "noc_transfer" {
            let src = *buffers
                .get(txt(&j["source"]["buffer_id"]))
                .ok_or_else(|| refuse("InvalidResource", "", "source absent"))?;
            let dst = *buffers
                .get(txt(&j["destination"]["buffer_id"]))
                .ok_or_else(|| refuse("InvalidResource", "", "destination absent"))?;
            for (region, buf) in [(&j["source"], src), (&j["destination"], dst)] {
                require(
                    num(&region["offset_bytes"]) as u128 + num(&region["size_bytes"]) as u128
                        <= num(&buf["size_bytes"]) as u128,
                    "InvalidTransfer",
                    "transfer range",
                )?;
            }
            require(
                j["source"]["size_bytes"] == j["destination"]["size_bytes"],
                "InvalidTransfer",
                "range size",
            )?;
            require(
                src["initial_residency"] == "preloaded"
                    || src["producer_id"]
                        .as_str()
                        .is_some_and(|pid| ancestors[id].contains(pid)),
                "InvalidDependency",
                "transfer source uninitialized",
            )?;
            require(
                dst["producer_id"] == j["id"],
                "InvalidDependency",
                "destination producer",
            )?;
            if j["kind"] == "dma" {
                let read = j["direction"] == "read";
                require(
                    src["space"] == if read { "hbm" } else { "sram" }
                        && dst["space"] == if read { "sram" } else { "hbm" },
                    "InvalidTransfer",
                    "DMA spaces",
                )?;
                let local = if read { dst } else { src };
                let engines = integer(&core["dma"]["engines"])?;
                require(
                    engines > 0 && num(&j["dma_engine_id"]) / engines == num(&local["core_id"]),
                    "InvalidResource",
                    "DMA engine core",
                )?;
                let mut cursor = 0;
                for f in arr(&j["fragments"]) {
                    require(
                        request_ids.insert(txt(&f["request_id"])),
                        "InvalidTransfer",
                        "duplicate request",
                    )?;
                    let route = routes
                        .get(txt(&f["route_id"]))
                        .ok_or_else(|| refuse("InvalidRoute", "", "fragment route"))?;
                    require(
                        num(&f["source_offset_bytes"])
                            == add(num(&j["source"]["offset_bytes"]), cursor)?
                            && num(&f["destination_offset_bytes"])
                                == add(num(&j["destination"]["offset_bytes"]), cursor)?,
                        "InvalidTransfer",
                        "fragment partition",
                    )?;
                    let address = if read {
                        add(num(&src["offset_bytes"]), num(&f["source_offset_bytes"]))?
                    } else {
                        add(
                            num(&dst["offset_bytes"]),
                            num(&f["destination_offset_bytes"]),
                        )?
                    };
                    require(
                        num(&f["channel_id"]) == (address / 256) % 8
                            && address % 256 + num(&f["payload_bytes"]) <= 256,
                        "InvalidTransfer",
                        "HBM stripe",
                    )?;
                    let attach = spec["memory"]["controllers"]
                        .get((num(&f["channel_id"]) / 2) as usize)
                        .ok_or_else(|| refuse("InvalidResource", "", "controller absent"))?;
                    let controller = add(
                        mul(num(&attach["attach"][0]), cols)?,
                        num(&attach["attach"][1]),
                    )?;
                    require(
                        route["source_core_id"] == local["core_id"]
                            && num(&route["destination_core_id"]) == controller,
                        "InvalidRoute",
                        "controller route",
                    )?;
                    cursor = add(cursor, num(&f["payload_bytes"]))?;
                }
                require(
                    cursor == num(&j["source"]["size_bytes"]),
                    "InvalidTransfer",
                    "complete fragment partition",
                )?;
            } else {
                require(
                    src["space"] == "sram" && dst["space"] == "sram" && src["id"] != dst["id"],
                    "InvalidTransfer",
                    "unicast buffers",
                )?;
                let route = routes
                    .get(txt(&j["route_id"]))
                    .ok_or_else(|| refuse("InvalidRoute", "", "unicast route"))?;
                require(
                    j["payload_bytes"] == j["source"]["size_bytes"]
                        && route["source_core_id"] == src["core_id"]
                        && route["destination_core_id"] == dst["core_id"],
                    "InvalidRoute",
                    "unicast route/payload",
                )?;
                // /2 uses one request inventory for DMA fragments and unicasts.
                require(
                    request_ids.insert(id),
                    "InvalidTransfer",
                    "duplicate request",
                )?;
            }
        }
    }
    // Completeness follows resource admission; never mask its stable earlier refusals.
    let owners = owner_map(spec, g)?;
    for j in arr(&g["jobs"]) {
        if j["kind"] == "barrier" {
            require(
                num(&j["owner_id"]) == owners[&format!("barrier:{}", txt(&j["id"]))],
                "InvalidResource",
                "canonical barrier owner",
            )?;
        }
        if j["kind"] != "compute" {
            continue;
        }
        for name in ["X", "W"] {
            let buf = buffers[txt(&j["operand_buffers"][name])];
            if buf["initial_residency"] == "preloaded" {
                continue;
            }
            let producer = jobs
                .get(buf["producer_id"].as_str().unwrap_or(""))
                .ok_or_else(|| refuse("InvalidTransfer", "", "missing operand producer"))?;
            require(
                (producer["kind"] == "dma" || producer["kind"] == "noc_transfer")
                    && producer["destination"]["buffer_id"] == buf["id"]
                    && producer["destination"]["offset_bytes"] == 0
                    && producer["destination"]["size_bytes"] == buf["size_bytes"],
                "InvalidTransfer",
                "complete operand population",
            )?;
        }
        if p["initial_state"] == "cold" {
            let buf = buffers[txt(&j["operand_buffers"]["Y"])];
            let mut writes: Vec<_> = jobs
                .values()
                .filter(|x| {
                    x["kind"] == "dma"
                        && x["direction"] == "write"
                        && x["source"]["buffer_id"] == buf["id"]
                })
                .map(|x| {
                    (
                        num(&x["source"]["offset_bytes"]),
                        num(&x["source"]["size_bytes"]),
                    )
                })
                .collect();
            writes.sort();
            let mut cursor = 0;
            for (offset, size) in writes {
                require(
                    offset == cursor,
                    "InvalidTransfer",
                    "cold output gap/overlap",
                )?;
                cursor = add(cursor, size)?;
            }
            require(
                cursor == num(&buf["size_bytes"]),
                "InvalidTransfer",
                "cold output incomplete",
            )?;
        }
    }
    Ok(())
}
fn hardware_model(v: &Value) -> Result<Hardware> {
    let h = &v["workload_closure"]["hardware_spec"];
    let c = &h["cores"]["core_type"];
    let d = &h["memory"]["dram"];
    let t = &d["timing"];
    require(
        !arr(&h["nocs"]).is_empty(),
        "UnsupportedHardware",
        "NoC absent",
    )?;
    let (n, bwden) = crate::hardware::ratio(&d["bw_bytes_per_s"]["value"])?;
    let refi = integer(&t["t_refi_cycles"])?;
    let rfc = integer(&t["t_rfc_cycles"])?;
    let channels = integer(&d["channels"])?;
    require(
        n > 0 && refi > rfc && channels == 8 && integer(&c["dma"]["request_bytes"])? == 256,
        "UnsupportedHardware",
        "channel/request/refresh law",
    )?;
    require(
        integer(&c["matrix_engine"]["array"]["rows"])? == 256
            && integer(&c["matrix_engine"]["array"]["cols"])? == 256,
        "UnsupportedHardware",
        "physical WS array",
    )?;
    // Cross-cancel before multiplication so reduced representable ratios do not overflow.
    let mut numer = [
        256u128,
        1_000_000_000_000,
        channels as u128,
        refi as u128,
        bwden,
    ];
    let mut denom = [n, (refi - rfc) as u128];
    for a in &mut numer {
        for b in &mut denom {
            let g = crate::wire::gcd(*a, *b);
            *a /= g;
            *b /= g;
        }
    }
    let product = |a: &[u128]| {
        a.iter()
            .try_fold(1u128, |n, x| n.checked_mul(*x))
            .ok_or_else(|| refuse("TimeOverflow", "", "channel ratio overflow"))
    };
    let operand_rate = integer(&c["matrix_engine"]["operand_bytes_per_cycle"])?;
    let port_rate = integer(&c["dma"]["bytes_per_cycle"])?;
    require(
        operand_rate > 0 && port_rate > 0,
        "UnsupportedHardware",
        "positive service rates",
    )?;
    Ok(Hardware {
        freq: [
            num(&v["freq_hz"]["core"]),
            num(&v["freq_hz"]["noc"]),
            num(&v["freq_hz"]["dram"]),
        ],
        operand_rate,
        port_rate,
        overhead: integer(&c["job_overhead_cycles"])?,
        wave_fill_drain: 510,
        hop_cycles: integer(&h["nocs"][0]["router_latency_cycles"])?,
        dram_latency: add(
            add(integer(&t["t_rp_cycles"])?, integer(&t["t_rcd_cycles"])?)?,
            integer(&t["t_cl_cycles"])?,
        )?,
        barrier_cycles: integer(&h["sync"]["barrier_latency_cycles"])?,
        credit_limit: integer(&c["dma"]["max_outstanding"])?,
        engines_per_core: integer(&c["dma"]["engines"])?,
        channel_step_num: product(&numer)?,
        channel_step_den: product(&denom)?,
    })
}
fn typed_graph(
    b: &Value,
    p: &Value,
    owners: &BTreeMap<String, u64>,
    hardware: &Hardware,
) -> Result<Graph> {
    let g = &p["task_graph"];
    let cols = integer(&b["hardware_spec"]["cores"]["grid"]["cols"])?;
    let job_ids: BTreeMap<_, _> = arr(&g["jobs"])
        .iter()
        .enumerate()
        .map(|(i, j)| (txt(&j["id"]), i))
        .collect();
    let route_ids: BTreeMap<_, _> = arr(&g["routes"])
        .iter()
        .enumerate()
        .map(|(i, j)| (txt(&j["id"]), i))
        .collect();
    let routes = arr(&g["routes"])
        .iter()
        .map(|r| {
            let core = num(&r["source_core_id"]);
            Route {
                hops: arr(&r["core_ids"]).len() as u64 - 1,
                owner: owners[&format!("router:0:{}:{}", core / cols, core % cols)],
            }
        })
        .collect();
    let mut jobs = Vec::new();
    for j in arr(&g["jobs"]) {
        let id = txt(&j["id"]).to_owned();
        let (kind, owner) = match txt(&j["kind"]) {
            "compute" => {
                let core = num(&j["core_id"]);
                (
                    TaskKind::Compute {
                        core,
                        m: num(&j["tile_extents"]["M"]),
                        k: num(&j["tile_extents"]["K"]),
                        n: num(&j["tile_extents"]["N"]),
                    },
                    owners[&format!("matrix:{core}")],
                )
            }
            "dma" => {
                let engine = num(&j["dma_engine_id"]);
                let core = engine / hardware.engines_per_core;
                let fragments = arr(&j["fragments"])
                    .iter()
                    .map(|f| Fragment {
                        id: txt(&f["request_id"]).into(),
                        payload: num(&f["payload_bytes"]),
                        channel: num(&f["channel_id"]),
                        route: route_ids[txt(&f["route_id"])],
                    })
                    .collect();
                (
                    TaskKind::Dma {
                        engine,
                        core,
                        write: j["direction"] == "write",
                        source: txt(&j["source"]["buffer_id"]).into(),
                        destination: txt(&j["destination"]["buffer_id"]).into(),
                        fragments,
                    },
                    owners[&format!("dma:{core}:{}", engine % hardware.engines_per_core)],
                )
            }
            "noc_transfer" => {
                let route = route_ids[txt(&j["route_id"])];
                let core = num(&g["routes"][route]["source_core_id"]);
                (
                    TaskKind::Unicast {
                        source: txt(&j["source"]["buffer_id"]).into(),
                        destination: txt(&j["destination"]["buffer_id"]).into(),
                        payload: num(&j["payload_bytes"]),
                        route,
                    },
                    owners[&format!("router:0:{}:{}", core / cols, core % cols)],
                )
            }
            "barrier" => (TaskKind::Barrier, owners[&format!("barrier:{id}")]),
            _ => return Err(refuse("TestOnlyScope", "", "unsupported component task")),
        };
        jobs.push(Task {
            id,
            op_id: j["op_id"].as_str().map(str::to_owned),
            owner,
            kind,
            raw: j.clone(),
        });
    }
    let buffers = arr(&g["buffers"])
        .iter()
        .map(|buf| {
            let space = txt(&buf["space"]);
            let owner = if space == "hbm" {
                owners["channel:0"]
            } else {
                owners[&format!(
                    "{}:{}",
                    if space == "sram" { "sram" } else { "matrix" },
                    num(&buf["core_id"])
                )]
            };
            Buffer {
                id: txt(&buf["id"]).into(),
                space: space.into(),
                owner,
                offset: num(&buf["offset_bytes"]),
                size: num(&buf["size_bytes"]),
                producer: buf["producer_id"].as_str().map(|id| job_ids[id]),
                consumers: arr(&buf["final_consumer_ids"])
                    .iter()
                    .map(|id| job_ids[txt(id)])
                    .collect(),
                persistent: buf["producer_id"].is_null()
                    || (space == "accumulator" && b["mapping_policy"]["version"] == "1"),
            }
        })
        .collect();
    let dependencies = arr(&g["dependencies"])
        .iter()
        .map(|d| (job_ids[txt(&d["before"])], job_ids[txt(&d["after"])]))
        .collect();
    Ok(Graph {
        jobs,
        buffers,
        routes,
        dependencies,
    })
}
