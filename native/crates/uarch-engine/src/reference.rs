//! R admission, resolved phase laws and observations in the existing native engine.
use crate::{
    carrier::{Result, refuse},
    component::{Phase, Ratio, Runtime},
    component_admission::{Admitted, Buffer, Graph, Task, TaskKind},
    wire,
};
use serde_json::{Value, json};
use std::collections::{BTreeMap, BTreeSet, VecDeque};
#[derive(Clone, Debug)]
pub(crate) struct ReferenceHardware {
    pub values: BTreeMap<String, Ratio>,
    pub window: u64,
    pub consumed: std::cell::RefCell<BTreeSet<String>>,
}
impl ReferenceHardware {
    pub fn p(&self, k: &str) -> Result<Ratio> {
        self.consumed.borrow_mut().insert(k.into());
        self.values
            .get(k)
            .copied()
            .ok_or_else(|| refuse("UnsupportedHardware", k, "missing service parameter"))
    }
}
#[derive(Clone, Debug)]
pub(crate) struct ReferenceSequence {
    pub phases: Vec<Phase>,
    pub hbm: bool,
    pub bytes: u64,
    pub write: bool,
}
fn require(ok: bool, code: &'static str, detail: &str) -> Result<()> {
    if ok {
        Ok(())
    } else {
        Err(refuse(code, "", detail))
    }
}
fn n(v: &Value) -> u64 {
    v.as_u64().expect("strict integer schema")
}
fn t(v: &Value) -> &str {
    v.as_str().expect("strict string schema")
}
fn a(v: &Value) -> &Vec<Value> {
    v.as_array().expect("strict array schema")
}
fn add(x: u64, y: u64) -> Result<u64> {
    crate::component::add(x, y)
}
fn mul(x: u64, y: u64) -> Result<u64> {
    crate::component::mul(x, y)
}
fn ratio(value: &Value) -> Result<Ratio> {
    let number = value
        .as_f64()
        .ok_or_else(|| refuse("InvalidCarrier", "", "number"))?;
    require(
        number.is_finite() && number > 0.0,
        "UnsupportedHardware",
        "positive finite service",
    )?;
    let text = wire::float_text(number).map_err(|e| refuse("InvalidCarrier", "", e))?;
    let (mantissa, exponent) = if let Some((x, e)) = text.split_once('e') {
        (
            x,
            e.parse::<i32>()
                .map_err(|_| refuse("TimeOverflow", "", "exponent"))?,
        )
    } else {
        (text.as_str(), 0)
    };
    let decimals = mantissa.split_once('.').map_or(0, |(_, x)| x.len() as i32);
    let digits = mantissa.replace('.', "");
    let mut numerator = digits
        .parse::<u128>()
        .map_err(|_| refuse("TimeOverflow", "", "decimal numerator"))?;
    let mut denominator = 1u128;
    let scale = exponent - decimals;
    let power = 10u128
        .checked_pow(scale.unsigned_abs())
        .ok_or_else(|| refuse("TimeOverflow", "", "decimal scale"))?;
    if scale >= 0 {
        numerator = numerator
            .checked_mul(power)
            .ok_or_else(|| refuse("TimeOverflow", "", "decimal product"))?;
    } else {
        denominator = power;
    }
    Ratio::new(numerator, denominator)
}
fn times(r: Ratio, k: u64) -> Result<Ratio> {
    Ratio::new(
        r.n.checked_mul(k as u128)
            .ok_or_else(|| refuse("TimeOverflow", "", "service product"))?,
        r.d,
    )
}
fn work(units: u64, rate: Ratio) -> Result<Ratio> {
    Ratio::new(
        (units as u128)
            .checked_mul(1_000_000_000_000)
            .and_then(|x| x.checked_mul(rate.d))
            .ok_or_else(|| refuse("TimeOverflow", "", "rate product"))?,
        rate.n,
    )
}
fn phase(name: &'static str, owner: u64, service: Ratio, occupies: bool) -> Phase {
    Phase {
        name,
        owner,
        category: if name == "r_mxu" || name == "r_vector" {
            "compute"
        } else {
            "memory"
        },
        domain: None,
        cycles: 0,
        service: Some(service),
        occupies,
        contended: occupies,
    }
}
fn sequence(phases: Vec<Phase>) -> ReferenceSequence {
    ReferenceSequence {
        phases,
        hbm: false,
        bytes: 0,
        write: false,
    }
}
fn identity(v: &Value, key: &str) -> Result<()> {
    let bytes = wire::canonical_large(v, Some(key)).map_err(|e| refuse("InvalidCarrier", "", e))?;
    require(
        v[key] == format!("sha256:{}", wire::hash(bytes.as_bytes())),
        "ContentHashMismatch",
        key,
    )
}
fn inc(counts: &mut BTreeMap<String, u64>, key: &str, amount: u64) -> Result<()> {
    let next = add(counts.get(key).copied().unwrap_or(0), amount)?;
    counts.insert(key.into(), next);
    Ok(())
}
fn primitive(h: &ReferenceHardware, p: &Value) -> Result<(Ratio, BTreeMap<String, u64>)> {
    let rows = n(&p["rows"]);
    let cols = n(&p["cols"]);
    let repeat = mul(n(&p["leading"]), n(&p["repeat"]))?;
    let kind = t(&p["kind"]);
    let mut counts = BTreeMap::new();
    let mut service = Ratio::integer(0);
    let tile = h.p("vector_tile_ps")?;
    if kind.starts_with("reduction_") {
        let mut active = cols;
        while active > 1 {
            active = active.div_ceil(2);
            let tiles = mul(mul(rows.div_ceil(8), active.div_ceil(128))?, repeat)?;
            let multiplier = h.p("reduction_cost_ratio")?;
            service = service.plus(Ratio::new(
                times(tile, tiles)?
                    .n
                    .checked_mul(multiplier.n)
                    .ok_or_else(|| refuse("TimeOverflow", "", "reduction"))?,
                times(tile, tiles)?
                    .d
                    .checked_mul(multiplier.d)
                    .ok_or_else(|| refuse("TimeOverflow", "", "reduction"))?,
            )?)?;
            inc(&mut counts, &format!("issued_{kind}"), mul(tiles, 1024)?)?;
        }
        inc(
            &mut counts,
            &format!("useful_{kind}"),
            mul(mul(rows, cols - 1)?, repeat)?,
        )?;
    } else {
        let tiles = mul(mul(rows.div_ceil(8), cols.div_ceil(128))?, repeat)?;
        let multiplier = match kind {
            "exp" => h.p("exp_cost_ratio")?,
            "reciprocal" => h.p("reciprocal_cost_ratio")?,
            "rsqrt" => h.p("rsqrt_cost_ratio")?,
            _ => Ratio::integer(1),
        };
        let scaled = times(tile, tiles)?;
        service = Ratio::new(
            scaled
                .n
                .checked_mul(multiplier.n)
                .ok_or_else(|| refuse("TimeOverflow", "", "primitive"))?,
            scaled
                .d
                .checked_mul(multiplier.d)
                .ok_or_else(|| refuse("TimeOverflow", "", "primitive"))?,
        )?;
        inc(
            &mut counts,
            &format!("useful_{kind}"),
            mul(mul(rows, cols)?, repeat)?,
        )?;
        inc(&mut counts, &format!("issued_{kind}"), mul(tiles, 1024)?)?;
    }
    Ok((service, counts))
}
fn task_sequences(h: &ReferenceHardware, j: &Value) -> Result<Vec<ReferenceSequence>> {
    Ok(match t(&j["kind"]) {
        "compute" => {
            let extent = &j["tile_extents"];
            let issued = mul(n(&extent["M"]), 128 * 128)?;
            let fill = h.p("matrix_fill_equivalent_macs")?;
            let amount = Ratio::integer(issued).plus(fill)?;
            let rate = h.p(if j["accumulator_dtype"] == "int32" {
                "int8_mxu_mac_per_s"
            } else {
                "bf16_mxu_mac_per_s"
            })?;
            let service = Ratio::new(
                amount
                    .n
                    .checked_mul(1_000_000_000_000)
                    .and_then(|x| x.checked_mul(rate.d))
                    .ok_or_else(|| refuse("TimeOverflow", "", "matrix"))?,
                amount
                    .d
                    .checked_mul(rate.n)
                    .ok_or_else(|| refuse("TimeOverflow", "", "matrix"))?,
            )?;
            vec![sequence(vec![
                phase("r_dispatch", 4, h.p("scalar_op_ps")?, true),
                phase("r_mxu", n(&j["matrix_engine_index"]), service, true),
            ])]
        }
        "vector" => {
            let mut phases = vec![
                phase("r_dispatch", 4, h.p("scalar_op_ps")?, true),
                phase("r_vector_setup", 5, h.p("vector_group_startup_ps")?, true),
            ];
            for p in a(&j["primitives"]) {
                if t(&p["kind"]).starts_with("reduction_") {
                    let mut active = n(&p["cols"]);
                    while active > 1 {
                        active = active.div_ceil(2);
                        let tiles = mul(
                            mul(n(&p["rows"]).div_ceil(8), active.div_ceil(128))?,
                            mul(n(&p["repeat"]), n(&p["leading"]))?,
                        )?;
                        let tile = times(h.p("vector_tile_ps")?, tiles)?;
                        let multiplier = h.p("reduction_cost_ratio")?;
                        let service = Ratio::new(
                            tile.n
                                .checked_mul(multiplier.n)
                                .ok_or_else(|| refuse("TimeOverflow", "", "stage"))?,
                            tile.d
                                .checked_mul(multiplier.d)
                                .ok_or_else(|| refuse("TimeOverflow", "", "stage"))?,
                        )?;
                        phases.push(phase("r_reduction", 5, service, true));
                    }
                } else {
                    phases.push(phase("r_vector", 5, primitive(h, p)?.0, true));
                }
            }
            for p in phases.iter_mut().skip(2) {
                p.contended = false;
            }
            vec![sequence(phases)]
        }
        "local_transfer" => vec![sequence(vec![phase(
            "r_vmem",
            6,
            work(n(&j["source"]["size_bytes"]), h.p("vmem_bytes_per_s")?)?,
            true,
        )])],
        "dma" => {
            let write = j["direction"] == "write";
            let mut spans = vec![];
            for span in a(&j["spans"]) {
                let mut left = n(&span["payload_bytes"]);
                while left > 0 {
                    let size = left.min(8192);
                    left -= size;
                    let mut phases = vec![
                        phase("r_latency", 7, h.p("hbm_latency_ps")?, false),
                        phase("r_hbm", 7, work(size, h.p("hbm_peak_bytes_per_s")?)?, true),
                    ];
                    let endpoint = phase("r_vmem", 6, work(size, h.p("vmem_bytes_per_s")?)?, true);
                    if write {
                        phases.insert(0, endpoint);
                    } else {
                        phases.push(endpoint);
                    }
                    spans.push(ReferenceSequence {
                        phases,
                        hbm: true,
                        bytes: size,
                        write,
                    });
                }
            }
            spans
        }
        "control" => vec![sequence(vec![phase(
            "r_control",
            4,
            times(h.p("scalar_op_ps")?, n(&j["instructions"]))?,
            true,
        )])],
        "barrier" => vec![sequence(vec![phase(
            "r_barrier",
            8,
            h.p("barrier_latency_ps")?,
            true,
        )])],
        _ => return Err(refuse("UnsupportedScope", "", "reference task kind")),
    })
}
fn task_counts(j: &Value, h: &ReferenceHardware) -> Result<BTreeMap<String, u64>> {
    let mut counts = BTreeMap::new();
    match t(&j["kind"]) {
        "compute" => {
            let d = &j["tile_extents"];
            let mut mac = mul(mul(n(&d["M"]), n(&d["K"]))?, n(&d["N"]))?;
            if let Some(pairs) = j["valid_pairs"].as_u64() {
                mac = mul(
                    pairs,
                    if j["member"] == "qk" {
                        n(&d["K"])
                    } else {
                        n(&d["N"])
                    },
                )?;
            }
            inc(&mut counts, "matrix_ops", mul(mac, 2)?)?;
            inc(
                &mut counts,
                "issued_matrix_ops",
                mul(n(&d["M"]), 2 * 128 * 128)?,
            )?;
        }
        "vector" => {
            for p in a(&j["primitives"]) {
                for (k, v) in primitive(h, p)?.1 {
                    inc(&mut counts, &k, v)?;
                }
            }
        }
        "dma" => {
            let bytes = n(&j["payload_bytes"]);
            inc(
                &mut counts,
                if j["direction"] == "read" {
                    "hbm_read_bytes"
                } else {
                    "hbm_write_bytes"
                },
                bytes,
            )?;
            inc(&mut counts, "vmem_bytes", bytes)?;
        }
        "local_transfer" => inc(&mut counts, "vmem_bytes", n(&j["source"]["size_bytes"]))?,
        "control" => inc(&mut counts, "scalar_instructions", n(&j["instructions"]))?,
        _ => {}
    }
    Ok(counts)
}
#[path = "reference_lifetimes.rs"]
mod lifetimes;
#[path = "reference_validation.rs"]
mod validation;
#[cfg(test)]
pub(crate) fn admit(input: &str) -> Result<Admitted> {
    admit_value(wire::parse(input).map_err(|e| refuse("InvalidJson", "", e))?)
}
pub(crate) fn admit_value(raw: Value) -> Result<Admitted> {
    let raw = crate::carrier::normalize_reference(raw)?;
    identity(&raw, "job_hash")?;
    let b = &raw["workload_closure"];
    identity(b, "bundle_hash")?;
    let point = &b["points"][0];
    identity(point, "payload_hash")?;
    let g = &point["task_graph"];
    identity(g, "graph_hash")?;
    identity(&b["source"], "source_hash")?;
    identity(&b["assumptions"], "assumptions_hash")?;
    require(
        raw["bundle_hash"] == b["bundle_hash"]
            && raw["point_hash"] == point["payload_hash"]
            && raw["admission"] == b["admission"],
        "ContentHashMismatch",
        "closure",
    )?;
    require(
        b["hardware_spec_hash"] == json!(crate::hardware::digest(&b["hardware_spec"])?),
        "HardwareMismatch",
        "hardware",
    )?;
    require(
        b["assumptions_hash"] == b["assumptions"]["assumptions_hash"],
        "ContentHashMismatch",
        "assumptions",
    )?;
    require(
        (raw["admission"]["invocation"] == "test")
            == (raw["admission"]["eligibility"] == "verification_only"),
        "AdmissionMismatch",
        "invocation",
    )?;
    require(
        (point["initial_state"] == "steady") == (n(&point["priming_iterations"]) > 0),
        "UnsupportedInitialState",
        "priming",
    )?;
    require(
        b["rank"]
            == json!({"collectives":"excluded","equivalent_ranks":[0],"kind":"balanced_tp_representative","rank_index":0,"tp":1}),
        "UnsupportedRankScope",
        "rank",
    )?;
    let mut values = BTreeMap::new();
    for (k, v) in b["hardware_spec"].as_object().unwrap() {
        if !v.is_object() {
            continue;
        }
        require(
            v["kind"] == "claim",
            "UnsupportedHardware",
            "reference claim required",
        )?;
        let value = ratio(&v["value"])?;
        let unit = if k.ends_with("_count")
            || k.ends_with("_rows")
            || k.ends_with("_cols")
            || k.ends_with("_outstanding")
        {
            "count"
        } else if k.ends_with("_capacity_bytes") {
            "byte"
        } else if k.ends_with("_mac_per_s") {
            "MAC/s"
        } else if k.ends_with("_ops_per_s") {
            "op/s"
        } else if k.ends_with("_bytes_per_s") {
            "byte/s"
        } else if k.ends_with("_ps") {
            "ps"
        } else if k.ends_with("_ratio") {
            "ratio"
        } else {
            "MAC-equivalent"
        };
        require(v["unit"] == unit, "UnsupportedHardware", "parameter unit")?;
        if unit == "count" || unit == "byte" {
            require(
                value.d == 1,
                "UnsupportedHardware",
                "integer capacity/count",
            )?;
        }
        values.insert(k.clone(), value);
    }
    let h = ReferenceHardware {
        window: values["hbm_max_outstanding"].ceil()?,
        values,
        consumed: std::cell::RefCell::new(BTreeSet::from(["hbm_max_outstanding".into()])),
    };
    for (key, value) in [
        ("tensorcore_count", 1),
        ("mxu_count", 4),
        ("mxu_rows", 128),
        ("mxu_cols", 128),
    ] {
        require(
            h.p(key)? == Ratio::integer(value),
            "UnsupportedHardware",
            key,
        )?;
    }
    for precision in ["bf16", "int8"] {
        let rate = h.p(&format!("{precision}_mxu_mac_per_s"))?;
        let peak = h.p(&format!("{precision}_peak_ops_per_s"))?;
        require(
            rate.n
                .checked_mul(8)
                .and_then(|x| x.checked_mul(peak.d))
                .ok_or_else(|| refuse("TimeOverflow", "", "chip peak"))?
                <= peak
                    .n
                    .checked_mul(rate.d)
                    .ok_or_else(|| refuse("TimeOverflow", "", "chip peak"))?,
            "UnsupportedHardware",
            "quarter-chip share",
        )?;
    }
    validation::validate(b, &h)?;
    let source = &b["source"];
    let ops: BTreeMap<_, _> = a(&source["ops"]).iter().map(|o| (t(&o["id"]), o)).collect();
    require(
        ops.len() == a(&source["ops"]).len(),
        "InvalidCoverage",
        "duplicate op",
    )?;
    if !source["coefficients"].is_null() {
        let c = &source["coefficients"];
        identity(c, "coefficients_hash")?;
        let width = n(&c["rotary_dim"]);
        let positions = n(&c["position_count"]);
        require(
            width >= 2 && width.is_multiple_of(2),
            "InvalidCoverage",
            "coefficient width",
        )?;
        for table in ["cos_bits", "sin_bits"] {
            require(
                a(&c[table]).len() as u64 == positions,
                "InvalidCoverage",
                "coefficient positions",
            )?;
            for row in a(&c[table]) {
                require(
                    a(row).len() as u64 == width / 2,
                    "InvalidCoverage",
                    "coefficient row",
                )?;
                for bits in a(row) {
                    let value = u32::from_str_radix(t(bits), 16)
                        .map_err(|_| refuse("InvalidCarrier", "", "coefficient bits"))?;
                    require(
                        value & 0x7f800000 != 0x7f800000,
                        "InvalidCarrier",
                        "nonfinite coefficient",
                    )?;
                }
            }
        }
        require(
            source["kv_key_encoding"]["coefficients_hash"] == c["coefficients_hash"],
            "CoefficientHashMismatch",
            "cache encoding",
        )?;
    }
    let mut buffers = vec![];
    let mut buffer_ids = BTreeMap::new();
    let task_ids: BTreeMap<_, _> = a(&g["jobs"])
        .iter()
        .enumerate()
        .map(|(i, j)| (t(&j["id"]), i + 1))
        .collect();
    require(
        task_ids.len() == a(&g["jobs"]).len(),
        "InvalidDependency",
        "duplicate job",
    )?;
    require(
        task_ids.len() <= 500_000,
        "CapacityExceeded",
        "reference graph task budget",
    )?;
    for space in ["hbm", "vmem", "smem"] {
        let budget = n(&b["assumptions"][format!("{space}_budget_bytes")]);
        let cap = h.p(&format!("{space}_capacity_bytes"))?;
        require(
            u128::from(budget) * cap.d <= cap.n,
            "CapacityExceeded",
            space,
        )?;
    }
    for (i, buf) in a(&g["buffers"]).iter().enumerate() {
        require(
            buffer_ids.insert(t(&buf["id"]), i).is_none(),
            "InvalidResource",
            "duplicate buffer",
        )?;
        let space = t(&buf["space"]);
        let end = add(n(&buf["offset_bytes"]), n(&buf["size_bytes"]))?;
        let budget = n(&b["assumptions"][format!("{space}_budget_bytes")]);
        require(
            end <= budget
                && Ratio::integer(budget).n * h.p(&format!("{space}_capacity_bytes"))?.d
                    <= h.p(&format!("{space}_capacity_bytes"))?.n,
            "CapacityExceeded",
            space,
        )?;
        require(
            buf["persistent"] != true || space == "smem",
            "InvalidResource",
            "persistent metadata",
        )?;
        let producer = if buf["producer_id"].is_null() {
            None
        } else {
            Some(
                *task_ids
                    .get(t(&buf["producer_id"]))
                    .ok_or_else(|| refuse("InvalidResource", "", "producer"))?,
            )
        };
        let consumers = a(&buf["final_consumer_ids"])
            .iter()
            .map(|x| {
                task_ids
                    .get(t(x))
                    .copied()
                    .ok_or_else(|| refuse("InvalidResource", "", "consumer"))
            })
            .collect::<Result<Vec<_>>>()?;
        buffers.push(Buffer {
            id: t(&buf["id"]).into(),
            space: space.into(),
            owner: 0,
            offset: n(&buf["offset_bytes"]),
            size: n(&buf["size_bytes"]),
            producer,
            consumers,
            persistent: buf["persistent"] == true,
        });
    }
    for space in ["hbm", "vmem", "smem"] {
        let mut ranges: Vec<_> = buffers
            .iter()
            .filter(|x| x.space == space)
            .map(|x| (x.offset, x.offset + x.size))
            .collect();
        ranges.sort();
        require(
            ranges.windows(2).all(|w| w[0].1 <= w[1].0),
            "LiveBufferAlias",
            space,
        )?;
    }
    let mut jobs = vec![Task {
        id: "@invocation".into(),
        op_id: None,
        owner: 8,
        kind: TaskKind::Reference {
            sequences: vec![sequence(vec![phase(
                "r_startup",
                8,
                h.p("kernel_startup_ps")?,
                true,
            )])],
        },
        raw: Value::Null,
    }];
    let mut dependencies = vec![];
    let mut indegree = vec![0usize; task_ids.len() + 1];
    let mut successors = vec![vec![]; task_ids.len() + 1];
    let mut edges = BTreeSet::new();
    for edge in a(&g["dependencies"]) {
        let before = *task_ids
            .get(t(&edge["before"]))
            .ok_or_else(|| refuse("InvalidDependency", "", "before"))?;
        let after = *task_ids
            .get(t(&edge["after"]))
            .ok_or_else(|| refuse("InvalidDependency", "", "after"))?;
        require(
            before != after && edges.insert((before, after)),
            "InvalidDependency",
            "duplicate/self",
        )?;
        dependencies.push((before, after));
        indegree[after] += 1;
        successors[before].push(after);
    }
    for (i, degree) in indegree.iter_mut().enumerate().skip(1) {
        if *degree == 0 {
            dependencies.push((0, i));
            *degree = 1;
            successors[0].push(i);
        }
    }
    let mut queue = VecDeque::from([0]);
    let mut visited = 0;
    let mut degree = indegree.clone();
    while let Some(i) = queue.pop_front() {
        visited += 1;
        for &j in &successors[i] {
            degree[j] -= 1;
            if degree[j] == 0 {
                queue.push_back(j);
            }
        }
    }
    require(visited == degree.len(), "InvalidDependency", "cycle")?;
    let mut seen_ops = BTreeSet::new();
    let mut coverage = BTreeMap::new();
    for c in a(&g["coverage"]) {
        require(
            coverage.insert(t(&c["job_id"]), c).is_none(),
            "InvalidCoverage",
            "duplicate coverage",
        )?;
    }
    let mut sequence_count = 0;
    for j in a(&g["jobs"]) {
        let op = t(&j["op_id"]);
        require(ops.contains_key(op), "InvalidCoverage", "unknown op")?;
        seen_ops.insert(op);
        if j["kind"] == "compute" {
            let c = coverage
                .remove(t(&j["id"]))
                .ok_or_else(|| refuse("InvalidCoverage", "", "missing tile"))?;
            for key in [
                "op_id",
                "group_id",
                "repeat_index",
                "tile_origin",
                "tile_extents",
            ] {
                require(c[key] == j[key], "InvalidCoverage", key)?;
            }
            let ext = &j["tile_extents"];
            require(
                n(&ext["M"]) <= 1024 && n(&ext["K"]) <= 128 && n(&ext["N"]) <= 128,
                "InvalidCoverage",
                "tile bounds",
            )?;
            require(
                j["physical_extents"] == json!({"M":n(&ext["M"]),"K":128,"N":128}),
                "InvalidCoverage",
                "physical tile",
            )?;
            require(
                mul(mul(n(&ext["M"]), n(&ext["N"]))?, 4)?
                    <= n(&b["assumptions"]["accumulator_window_bytes"]),
                "CapacityExceeded",
                "partial",
            )?;
            for name in j["operand_buffers"]
                .as_object()
                .unwrap()
                .values()
                .chain(std::iter::once(&j["accumulator_buffer_id"]))
            {
                require(
                    buffer_ids.contains_key(t(name)),
                    "InvalidResource",
                    "operand buffer",
                )?;
            }
        }
        if j["kind"] == "dma" || j["kind"] == "local_transfer" {
            let size = if j["kind"] == "dma" {
                n(&j["payload_bytes"])
            } else {
                n(&j["source"]["size_bytes"])
            };
            if j["kind"] == "local_transfer" {
                require(
                    size == n(&j["destination"]["size_bytes"]),
                    "InvalidTransfer",
                    "extent",
                )?;
            }
            for end in ["source", "destination"] {
                let buf = *buffer_ids
                    .get(t(&j[end]["buffer_id"]))
                    .ok_or_else(|| refuse("InvalidResource", "", "range buffer"))?;
                require(
                    add(n(&j[end]["offset_bytes"]), n(&j[end]["size_bytes"]))? <= buffers[buf].size,
                    "InvalidTransfer",
                    "range bounds",
                )?;
            }
            if j["kind"] == "dma" {
                let mut sum = 0;
                for span in a(&j["spans"]) {
                    sum = add(sum, n(&span["payload_bytes"]))?;
                    for end in ["source", "destination"] {
                        let buf = buffer_ids[t(&j[end]["buffer_id"])];
                        require(
                            n(&span[format!("{end}_offset_bytes")]) >= n(&j[end]["offset_bytes"])
                                && add(
                                    n(&span[format!("{end}_offset_bytes")]),
                                    n(&span["payload_bytes"]),
                                )? <= add(n(&j[end]["offset_bytes"]), n(&j[end]["size_bytes"]))?
                                    .min(buffers[buf].size),
                            "InvalidTransfer",
                            "span bounds",
                        )?;
                    }
                }
                require(sum == size, "InvalidTransfer", "span coverage")?;
                let src = &buffers[buffer_ids[t(&j["source"]["buffer_id"])]];
                let dst = &buffers[buffer_ids[t(&j["destination"]["buffer_id"])]];
                require(
                    if j["direction"] == "read" {
                        src.space == "hbm" && dst.space == "vmem"
                    } else {
                        src.space == "vmem" && dst.space == "hbm"
                    },
                    "InvalidTransfer",
                    "memory spaces",
                )?;
            }
        }
        let sequences = task_sequences(&h, j)?;
        sequence_count += sequences.len();
        require(
            sequence_count <= 2_000_000,
            "CapacityExceeded",
            "reference sequence budget",
        )?;
        jobs.push(Task {
            id: t(&j["id"]).into(),
            op_id: Some(op.into()),
            owner: 0,
            kind: TaskKind::Reference { sequences },
            raw: json!({"kind":j["kind"]}),
        });
    }
    require(
        coverage.is_empty() && seen_ops.len() == ops.len(),
        "MissingCoverage",
        "source completeness",
    )?;
    lifetimes::validate(g)?;
    validation::transfers(b)?;
    Ok(Admitted {
        raw,
        graph: Graph {
            jobs,
            buffers,
            routes: vec![],
            dependencies,
        },
        hardware: None,
        reference: Some(h),
        owners: BTreeMap::new(),
    })
}
fn semantic_counts(op: &Value) -> Result<(u64, u64)> {
    let d = &op["spec"]["dimensions"];
    let kind = t(&op["spec"]["operator"]);
    Ok(match kind {
        "q_projection" | "k_projection" | "v_projection" | "output_projection" | "ffn_up"
        | "ffn_gate" | "ffn_down" => (mul(2, mul(mul(n(&d["M"]), n(&d["K"]))?, n(&d["N"]))?)?, 0),
        "normalization" | "activation" => (0, mul(6, mul(n(&d["M"]), n(&d["D"]))?)?),
        "residual_addition" => (0, mul(n(&d["M"]), n(&d["D"]))?),
        "rotary_embedding" => (
            0,
            mul(
                3,
                mul(mul(mul(n(&d["B"]), n(&d["S"]))?, n(&d["H"]))?, n(&d["R"]))?,
            )?,
        ),
        "attention_fused" => {
            let s = n(&d["S"]);
            let t = n(&d["T"]);
            let pairs = mul(
                mul(n(&d["B"]), n(&d["Hq"]))?,
                if s == t {
                    mul(s, add(s, 1)?)? / 2
                } else {
                    mul(s, t)?
                },
            )?;
            (mul(4, mul(pairs, n(&d["D"]))?)?, mul(5, pairs)?)
        }
        "stream_read_sum" => (0, n(&d["E"]) - 1),
        "scalar_add" => (0, 1),
        _ => (0, 0),
    })
}
pub(crate) fn construct(v: &Admitted, r: &Runtime) -> Result<Value> {
    let mut counts = BTreeMap::new();
    let mut per_op: BTreeMap<String, BTreeMap<String, u64>> = BTreeMap::new();
    for (index, task) in v.graph.jobs.iter().enumerate() {
        if let Some(op) = &task.op_id {
            let raw = &v.raw["workload_closure"]["points"][0]["task_graph"]["jobs"][index - 1];
            for (k, value) in task_counts(raw, v.reference.as_ref().unwrap())? {
                inc(&mut counts, &k, value)?;
                inc(per_op.entry(op.clone()).or_default(), &k, value)?;
            }
        }
    }
    for op in a(&v.raw["workload_closure"]["source"]["ops"]) {
        let (matrix, vector) = semantic_counts(op)?;
        for (key, value) in [
            ("semantic_matrix_ops", matrix),
            ("semantic_vector_ops", vector),
        ] {
            inc(&mut counts, key, value)?;
            inc(per_op.entry(t(&op["id"]).into()).or_default(), key, value)?;
        }
    }
    let activities:Vec<_>=r.activities.iter().map(|x|json!({"task":x.job,"sequence":x.sequence,"phase":x.phase.name,"owner":x.phase.owner,"ready_ps":x.ready,"start_ps":x.start,"end_ps":x.end,"occupies":x.phase.occupies,"ratio_start":x.ratio.map(|p|[p.0.n,p.0.d]),"ratio_end":x.ratio.map(|p|[p.1.n,p.1.d]),"causes":x.causes})).collect();
    let mut path = vec![];
    let mut current = r
        .activities
        .iter()
        .enumerate()
        .rev()
        .find(|(_, x)| x.end == r.duration)
        .map(|(i, _)| i);
    let mut stop = r.duration;
    while let Some(i) = current {
        let x = &r.activities[i];
        if stop > x.start {
            path.push(json!({"activity":i,"start_ps":x.start,"end_ps":stop,"cause":"service"}));
        }
        if x.start == 0 {
            break;
        }
        let cause = x
            .causes
            .iter()
            .min_by_key(|(a, k)| (if *k == "issue_spacing" { 1 } else { 0 }, *a))
            .copied()
            .ok_or_else(|| refuse("IncompleteObservations", "", "critical cause missing"))?;
        if cause.1 == "issue_spacing" {
            let previous = &r.activities[cause.0];
            path.push(json!({"activity":i,"start_ps":previous.start,"end_ps":x.start,"cause":"issue_spacing"}));
            stop = previous.start;
        } else {
            stop = r.activities[cause.0].end;
        }
        current = Some(cause.0);
    }
    path.reverse();
    let point = &v.raw["workload_closure"]["points"][0];
    let source = &v.raw["workload_closure"]["source"];
    let (metadata_before, metadata_after) = r.reference_metadata();
    let state_before = json!({"context_before":source["context_before"],"context_after":source["context_after"],"persistent_metadata":metadata_before,"reload":"payload-every-invocation"});
    let state_after = json!({"context_before":source["context_before"],"context_after":source["context_after"],"persistent_metadata":metadata_after,"reload":"payload-every-invocation"});
    let stubs: Vec<_> = v.raw["workload_closure"]["hardware_spec"]
        .as_object()
        .unwrap()
        .iter()
        .filter(|(k, x)| {
            x["provenance"] == "stub"
                && v.reference.as_ref().unwrap().consumed.borrow().contains(*k)
        })
        .map(|(k, _)| k.clone())
        .collect();
    let mut result = json!({"protocol":"uarch-engine/5","job_hash":v.raw["job_hash"],"bundle_hash":v.raw["bundle_hash"],"point_hash":v.raw["point_hash"],"engine":v.raw["engine"],"duration_ps":r.duration,"counts":counts,"per_op_counts":per_op,"consumed_stubs":stubs,"calibration":"stub","error":"unknown","energy":"unverified","physical_transactions":null,"energy_pj":null,
        "observations":{"format":"uarch-native-observations/4","activities":activities,"jobs":r.jobs.iter().map(|j|[j.ready.unwrap(),j.start.unwrap(),j.end.unwrap()]).collect::<Vec<_>>(),
        "sequences":r.sequences.iter().map(|s|[s.job as u64,s.issue.unwrap(),s.end.unwrap(),s.payload]).collect::<Vec<_>>(),
        "allocation_intervals":r.allocations.iter().map(|x|[x.start.unwrap_or(0),x.end.unwrap_or(r.duration)]).collect::<Vec<_>>(),"critical_path":path,
        "priming_iterations":point["priming_iterations"],"state_before":crate::hardware::digest(&state_before)?,"state_after":crate::hardware::digest(&state_after)?,"max_live_events":r.max_live_events,"persistent_before":metadata_before,"persistent_after":metadata_after,"context_before":source["context_before"],"context_after":source["context_after"]}});
    result["result_hash"] = json!(format!(
        "sha256:{}",
        wire::hash(
            wire::canonical_large(&result, None)
                .map_err(|e| refuse("InternalError", "", e))?
                .as_bytes()
        )
    ));
    Ok(result)
}
