//! Independent mathematical closure checks before any native event is dispatched.
use super::*;
fn dimensions(op: &Value) -> &Value {
    &op["spec"]["dimensions"]
}
fn typed(tasks: &[&Value], h: &ReferenceHardware) -> Result<BTreeMap<String, u64>> {
    let mut result = BTreeMap::new();
    for task in tasks {
        if task["kind"] == "vector" {
            for p in a(&task["primitives"]) {
                for (key, value) in primitive(h, p)?.1 {
                    if let Some(kind) = key.strip_prefix("useful_") {
                        inc(&mut result, kind, value)?;
                    }
                }
            }
        }
    }
    result.retain(|_, v| *v > 0);
    Ok(result)
}
fn expected(op: &Value) -> Result<BTreeMap<String, u64>> {
    let d = dimensions(op);
    let kind = t(&op["spec"]["operator"]);
    let mut c = BTreeMap::new();
    let rows = d["M"].as_u64().unwrap_or(1);
    let cols = d["D"].as_u64().unwrap_or(1);
    let e = mul(rows, cols)?;
    let pairs: Vec<(&str, u64)> = match kind {
        "q_projection" | "k_projection" | "v_projection" | "output_projection" | "ffn_up"
        | "ffn_gate" | "ffn_down" => vec![(
            "cast",
            if op["spec"]["operands"]["X"]["dtype"] == "bf16" {
                mul(n(&d["M"]), n(&d["N"]))?
            } else {
                0
            },
        )],
        "normalization" => vec![
            ("cast", add(mul(2, e)?, cols)?),
            ("multiply", add(mul(3, e)?, rows)?),
            ("reduction_sum", mul(rows, cols - 1)?),
            ("add", rows),
            ("rsqrt", rows),
        ],
        "residual_addition" => vec![("cast", mul(3, e)?), ("add", e)],
        "activation" => vec![
            ("cast", mul(3, e)?),
            ("negate", e),
            ("exp", e),
            ("add", e),
            ("reciprocal", e),
            ("multiply", mul(2, e)?),
        ],
        "rotary_embedding" => {
            let e = mul(mul(mul(n(&d["B"]), n(&d["S"]))?, n(&d["H"]))?, n(&d["R"]))?;
            vec![
                ("cast", mul(2, e)?),
                ("multiply", mul(2, e)?),
                ("add", e / 2),
                ("subtract", e / 2),
            ]
        }
        "scalar_add" => vec![("add", 1)],
        "stream_read_sum" => vec![("cast", n(&d["E"])), ("reduction_sum", n(&d["E"]) - 1)],
        "stream_fill" => vec![("broadcast", n(&d["E"]))],
        "attention_fused" => {
            let rows = mul(mul(n(&d["B"]), n(&d["Hq"]))?, n(&d["S"]))?;
            let e = mul(rows, n(&d["T"]))?;
            let reduction = mul(rows, n(&d["T"]) - 1)?;
            vec![
                ("multiply", mul(2, e)?),
                ("select", e),
                ("reduction_max", reduction),
                ("subtract", e),
                ("exp", e),
                ("reduction_sum", reduction),
                ("reciprocal", rows),
                ("cast", add(e, mul(rows, n(&d["D"]))?)?),
            ]
        }
        "kv_write" | "paged_gather" | "stream_copy" => vec![],
        _ => return Err(refuse("UnsupportedScope", "", "operator")),
    };
    for (k, v) in pairs {
        if v > 0 {
            c.insert(k.into(), v);
        }
    }
    Ok(c)
}
fn op_dimensions(op: &Value) -> Result<()> {
    let d = dimensions(op);
    let kind = t(&op["spec"]["operator"]);
    let required: &[&str] = match kind {
        "q_projection" | "k_projection" | "v_projection" | "output_projection" | "ffn_up"
        | "ffn_gate" | "ffn_down" => &["M", "K", "N"],
        "normalization" | "residual_addition" | "activation" | "scalar_add" => &["M", "D"],
        "rotary_embedding" => &["B", "S", "H", "D", "R"],
        "stream_read_sum" | "stream_fill" | "stream_copy" => &["E", "One"],
        "paged_gather" => &["B", "S", "T", "H", "D", "P"],
        "kv_write" | "attention_fused" => &["B", "S", "T", "Hq", "H", "D", "P"],
        _ => return Err(refuse("UnsupportedScope", "", "operator")),
    };
    require(
        d.as_object()
            .unwrap()
            .keys()
            .map(String::as_str)
            .collect::<BTreeSet<_>>()
            == required.iter().copied().collect(),
        "InvalidCoverage",
        "operator dimensions",
    )?;
    require(
        n(&op["work_repeat"]) == 1 && n(&op["weight_copies"]) == 1,
        "UnsupportedScope",
        "one selected group",
    )?;
    let limits = BTreeMap::from([
        ("M", 4096),
        ("K", 14336),
        ("N", 14336),
        ("B", 32),
        ("S", 2049),
        ("T", 2049),
        ("Hq", 32),
        ("H", 32),
        ("D", 14336),
        ("R", 128),
        ("P", 32),
        ("E", 134217728),
        ("One", 1),
    ]);
    for (key, value) in d.as_object().unwrap() {
        require(
            n(value) <= limits[key.as_str()],
            "UnsupportedShape",
            "bounded reference dimensions",
        )?;
    }
    for operand in op["spec"]["operands"].as_object().unwrap().values() {
        for axis in a(&operand["dimensions"]) {
            require(
                d.get(t(axis)).is_some(),
                "InvalidCoverage",
                "undefined operand axis",
            )?;
        }
    }
    if !op["kv_access"].is_null() {
        let kv = &op["kv_access"];
        let length = n(&d["T"]);
        let page = n(&d["P"]);
        require(
            n(&kv["context_tokens"]) == length
                && n(&kv["block_size_tokens"]) == page
                && n(&kv["pages_per_sequence"]) == length.div_ceil(page)
                && n(&kv["last_page_valid_tokens"]) == (length - 1) % page + 1,
            "InvalidCoverage",
            "KV valid tail",
        )?;
    }
    if kind == "scalar_add" {
        require(
            n(&d["M"]) == 1 && n(&d["D"]) == 1,
            "InvalidCoverage",
            "scalar shape",
        )?;
    }
    Ok(())
}
pub(super) fn validate(b: &Value, h: &ReferenceHardware) -> Result<()> {
    let source = &b["source"];
    require(
        source["attention_mask"] == "causal",
        "UnsupportedScope",
        "R selected causal scope",
    )?;
    let g = &b["points"][0]["task_graph"];
    let chunk = n(&b["assumptions"]["matrix_m_chunk"]);
    let ops = a(&source["ops"]);
    for op in ops {
        op_dimensions(op)?;
    }
    let ids: BTreeSet<_> = ops.iter().map(|o| t(&o["id"])).collect();
    let mut kinds = BTreeMap::new();
    let mut scalar_keys = BTreeSet::new();
    for op in ops {
        let kind = t(&op["spec"]["operator"]);
        operator_inputs(source, op)?;
        if kind == "normalization" {
            scalar_keys.insert("rmsnorm_epsilon");
            require(
                source["scalar_inputs"]["rmsnorm_epsilon"]
                    .as_f64()
                    .is_some_and(|x| x > 0.0),
                "InvalidCoverage",
                "RMSNorm epsilon",
            )?;
        }
        if kind == "attention_fused" {
            scalar_keys.insert("attention_scale");
            let scale = 1.0 / (n(&dimensions(op)["D"]) as f64).sqrt();
            require(
                source["scalar_inputs"]["attention_scale"]
                    .as_f64()
                    .is_some_and(|x| (x - scale).abs() <= f64::EPSILON * scale),
                "InvalidCoverage",
                "attention scale",
            )?;
        }
        if op["spec"]["operands"]["X"]["dtype"] == "int8" {
            scalar_keys.extend(["raw_int8_min", "raw_int8_max"]);
            require(
                source["scalar_inputs"]["raw_int8_min"].as_f64() == Some(-7.0)
                    && source["scalar_inputs"]["raw_int8_max"].as_f64() == Some(7.0),
                "UnsupportedPrecision",
                "raw INT8 bounds",
            )?;
        }
        *kinds.entry(kind).or_insert(0) += 1;
        require(
            a(&op["depends_on"])
                .iter()
                .all(|x| ids.contains(t(x)) && x != &op["id"]),
            "InvalidDependency",
            "mathematical dependency",
        )?;
        let tasks: Vec<_> = a(&g["jobs"])
            .iter()
            .filter(|j| j["op_id"] == op["id"])
            .collect();
        require(
            !tasks.is_empty() && typed(&tasks, h)? == expected(op)?,
            "InvalidCoverage",
            "typed operator work",
        )?;
        for task in &tasks {
            if task["kind"] == "vector" {
                for p in a(&task["primitives"]) {
                    require(
                        if p["kind"] == "cast" {
                            (p["source_dtype"] == "bf16" && p["destination_dtype"] == "fp32")
                                || (p["source_dtype"] == "fp32" && p["destination_dtype"] == "bf16")
                        } else {
                            p["source_dtype"].is_null() && p["destination_dtype"].is_null()
                        },
                        "UnsupportedPrecision",
                        "primitive conversion",
                    )?;
                }
            }
        }
        let d = dimensions(op);
        let dots = matches!(
            kind,
            "q_projection"
                | "k_projection"
                | "v_projection"
                | "output_projection"
                | "ffn_up"
                | "ffn_gate"
                | "ffn_down"
        );
        if dots || kind == "attention_fused" {
            let mut actual = BTreeSet::new();
            for j in tasks.iter().filter(|j| j["kind"] == "compute") {
                let member = t(&j["member"]);
                let leading = n(&j["leading_index"]);
                let (m, k, nn) = if dots {
                    (n(&d["M"]), n(&d["K"]), n(&d["N"]))
                } else if member == "qk" {
                    (n(&d["S"]), n(&d["D"]), n(&d["T"]))
                } else {
                    require(member == "av", "InvalidCoverage", "attention member")?;
                    (n(&d["S"]), n(&d["T"]), n(&d["D"]))
                };
                let origin = &j["tile_origin"];
                let ext = &j["tile_extents"];
                for (axis, step, size) in [("M", chunk, m), ("K", 128, k), ("N", 128, nn)] {
                    let start = n(&origin[axis]);
                    require(
                        start < size
                            && start.is_multiple_of(step)
                            && n(&ext[axis]) == step.min(size - start),
                        "InvalidCoverage",
                        "tile partition",
                    )?;
                }
                require(
                    actual.insert((
                        member,
                        leading,
                        n(&origin["M"]),
                        n(&origin["K"]),
                        n(&origin["N"]),
                    )),
                    "InvalidCoverage",
                    "overlapping tile",
                )?;
                let expected_owner =
                    (n(&origin["M"]) / chunk * nn.div_ceil(128) + n(&origin["N"]) / 128) % 4;
                require(
                    n(&j["matrix_engine_index"]) == expected_owner,
                    "InvalidResource",
                    "stable MXU placement",
                )?;
                if dots {
                    require(
                        member == "dot" && leading == 0 && j["valid_pairs"].is_null(),
                        "InvalidCoverage",
                        "dot member",
                    )?;
                    let precision = &op["spec"]["operands"]["X"]["dtype"];
                    require(
                        (precision == "bf16" || precision == "int8")
                            && op["spec"]["operands"]["W"]["dtype"] == *precision,
                        "UnsupportedPrecision",
                        "dot precision",
                    )?;
                    require(
                        j["operand_dtypes"]["X"] == *precision
                            && j["operand_dtypes"]["W"] == *precision,
                        "UnsupportedPrecision",
                        "mapped precision",
                    )?;
                    require(
                        j["accumulator_dtype"]
                            == if precision == "int8" { "int32" } else { "fp32" },
                        "UnsupportedPrecision",
                        "accumulator",
                    )?;
                    if precision == "int8" {
                        require(k <= 4096, "UnsupportedShape", "INT8 safe accumulation")?;
                    }
                } else {
                    require(
                        leading < mul(n(&d["B"]), n(&d["Hq"]))?,
                        "InvalidCoverage",
                        "attention leading",
                    )?;
                    let causal = n(&d["S"]) == n(&d["T"]);
                    let mut pairs = 0;
                    if causal {
                        let axis = if member == "qk" { "N" } else { "K" };
                        for row in 0..n(&ext["M"]) {
                            pairs += n(&ext[axis])
                                .min((n(&origin["M"]) + row + 1).saturating_sub(n(&origin[axis])));
                        }
                    }
                    require(
                        if causal {
                            j["valid_pairs"] == json!(pairs)
                        } else {
                            j["valid_pairs"].is_null()
                        },
                        "InvalidCoverage",
                        "causal pairs",
                    )?;
                }
            }
            let expected = if dots {
                mul(
                    mul(n(&d["M"]).div_ceil(chunk), n(&d["K"]).div_ceil(128))?,
                    n(&d["N"]).div_ceil(128),
                )?
            } else {
                mul(
                    mul(
                        mul(mul(n(&d["B"]), n(&d["Hq"]))?, n(&d["S"]).div_ceil(chunk))?,
                        n(&d["D"]).div_ceil(128),
                    )?,
                    mul(n(&d["T"]).div_ceil(128), 2)?,
                )?
            };
            require(
                actual.len() as u64 == expected,
                "InvalidCoverage",
                "missing matrix partition",
            )?;
        } else {
            require(
                !tasks.iter().any(|j| j["kind"] == "compute"),
                "InvalidCoverage",
                "unexpected matrix",
            )?;
        }
        if matches!(kind, "paged_gather" | "kv_write" | "attention_fused") {
            let page_count = n(&d["T"]).div_ceil(n(&d["P"]));
            let pages: Vec<_> = a(&source["page_indices"]).iter().map(n).collect();
            let mut sorted = pages.clone();
            sorted.sort_unstable();
            require(
                sorted == (0..page_count).collect::<Vec<_>>(),
                "InvalidCoverage",
                "page permutation",
            )?;
            if kind != "attention_fused" {
                let lookup: Vec<_> = tasks.iter().filter(|j| j["kind"] == "control").collect();
                require(
                    lookup.len() == 1
                        && lookup[0]["page_entries"] == source["page_indices"]
                        && n(&lookup[0]["instructions"]) == page_count,
                    "InvalidCoverage",
                    "page lookup work",
                )?;
            }
        }
        if kind == "rotary_embedding" {
            let r = &op["rotary"];
            let c = &source["coefficients"];
            require(
                !r.is_null() && !c.is_null() && a(&op["depends_on"]).contains(&r["input_op_id"]),
                "InvalidCoverage",
                "rotary input",
            )?;
            require(
                r["coefficients_hash"] == c["coefficients_hash"]
                    && c["coefficients_hash"] == source["kv_key_encoding"]["coefficients_hash"],
                "CoefficientHashMismatch",
                "rotary data identity",
            )?;
            require(
                n(&d["R"]) == n(&c["rotary_dim"]) && n(&d["R"]) == n(&d["D"]),
                "InvalidCoverage",
                "rotary extent",
            )?;
            require(
                n(&source["context_after"]) <= n(&c["position_count"])
                    && n(&source["context_after"]).checked_sub(n(&source["context_before"]))
                        == Some(n(&d["S"])),
                "InvalidCoverage",
                "position extent",
            )?;
            let producer = ops
                .iter()
                .find(|x| x["id"] == r["input_op_id"])
                .ok_or_else(|| refuse("InvalidCoverage", "", "rotary producer"))?;
            require(
                producer["spec"]["operator"] == format!("{}_projection", t(&r["target"]))
                    && n(&dimensions(producer)["N"]) == mul(n(&d["H"]), n(&d["D"]))?
                    && n(&dimensions(producer)["M"]) == mul(n(&d["B"]), n(&d["S"]))?,
                "InvalidCoverage",
                "rotary projection join",
            )?;
            let positions: Vec<_> =
                (n(&source["context_before"])..n(&source["context_after"])).collect();
            require(
                r["position_ids"] == json!(vec![positions; n(&d["B"]) as usize]),
                "InvalidCoverage",
                "positions",
            )?;
        }
    }
    require(
        source["scalar_inputs"]
            .as_object()
            .unwrap()
            .keys()
            .map(String::as_str)
            .collect::<BTreeSet<_>>()
            == scalar_keys,
        "InvalidCoverage",
        "numerical source inputs",
    )?;
    if source["scope"] == "decoder" {
        let expected = BTreeMap::from([
            ("normalization", 2),
            ("residual_addition", 2),
            ("q_projection", 1),
            ("k_projection", 1),
            ("v_projection", 1),
            ("rotary_embedding", 2),
            ("kv_write", 1),
            ("attention_fused", 1),
            ("output_projection", 1),
            ("ffn_up", 1),
            ("ffn_gate", 1),
            ("activation", 1),
            ("ffn_down", 1),
        ]);
        require(kinds == expected, "MissingCoverage", "complete decoder")?;
        decoder_roles(source)?;
        let mut targets: Vec<_> = ops
            .iter()
            .filter(|o| o["spec"]["operator"] == "rotary_embedding")
            .map(|o| t(&o["rotary"]["target"]))
            .collect();
        targets.sort();
        require(
            targets == ["k", "q"],
            "InvalidCoverage",
            "one Q and K rotation",
        )?;
    }
    Ok(())
}

fn decoder_roles(source: &Value) -> Result<()> {
    let ops = a(&source["ops"]);
    let names = |kind: &str| -> BTreeSet<&str> {
        ops.iter()
            .filter(|o| o["spec"]["operator"] == kind)
            .map(|o| t(&o["id"]))
            .collect()
    };
    let parents = |op: &Value| -> BTreeSet<String> {
        a(&op["depends_on"]).iter().map(|x| t(x).into()).collect()
    };
    let check = |op: &Value, expected: BTreeSet<&str>| {
        require(
            parents(op) == expected.into_iter().map(str::to_owned).collect(),
            "InvalidCoverage",
            "decoder dependency roles",
        )
    };
    let root: Vec<_> = ops
        .iter()
        .filter(|o| o["spec"]["operator"] == "normalization" && a(&o["depends_on"]).is_empty())
        .collect();
    require(root.len() == 1, "InvalidCoverage", "first norm")?;
    let first = t(&root[0]["id"]);
    let second: Vec<_> = ops
        .iter()
        .filter(|o| o["spec"]["operator"] == "normalization" && t(&o["id"]) != first)
        .collect();
    require(second.len() == 1, "InvalidCoverage", "second norm")?;
    let rotary: BTreeMap<_, _> = ops
        .iter()
        .filter(|o| o["spec"]["operator"] == "rotary_embedding")
        .map(|o| (t(&o["rotary"]["target"]), t(&o["id"])))
        .collect();
    require(
        rotary.len() == 2 && rotary.contains_key("q") && rotary.contains_key("k"),
        "InvalidCoverage",
        "rotary roles",
    )?;
    let output = names("output_projection");
    let residual1: Vec<_> = ops
        .iter()
        .filter(|o| {
            o["spec"]["operator"] == "residual_addition"
                && parents(o) == output.iter().map(|s| (*s).to_owned()).collect()
        })
        .collect();
    require(residual1.len() == 1, "InvalidCoverage", "first residual")?;
    let residual = t(&residual1[0]["id"]);
    check(second[0], BTreeSet::from([residual]))?;
    for op in ops {
        match t(&op["spec"]["operator"]) {
            "q_projection" | "k_projection" | "v_projection" => check(op, BTreeSet::from([first]))?,
            "output_projection" => check(op, names("attention_fused"))?,
            "ffn_down" => check(op, names("activation"))?,
            "ffn_up" | "ffn_gate" => check(op, BTreeSet::from([t(&second[0]["id"])]))?,
            "activation" => check(
                op,
                names("ffn_up").union(&names("ffn_gate")).copied().collect(),
            )?,
            "kv_write" => {
                let mut p = names("v_projection");
                p.insert(rotary["k"]);
                check(op, p)?;
            }
            "attention_fused" => {
                let mut p = names("kv_write");
                p.insert(rotary["q"]);
                check(op, p)?;
            }
            "residual_addition" if t(&op["id"]) != residual => {
                let mut p = names("ffn_down");
                p.insert(residual);
                check(op, p)?;
            }
            _ => {}
        }
    }
    Ok(())
}

pub(super) fn transfers(b: &Value) -> Result<()> {
    let g = &b["points"][0]["task_graph"];
    let buffers: BTreeMap<_, _> = a(&g["buffers"]).iter().map(|x| (t(&x["id"]), x)).collect();
    // Count the required store/read pair per K slice, including the final read.
    // Byte-lifetime validation separately enforces producers and reuse ordering.
    let mut expected: BTreeMap<(&str, &str, u64), u64> = BTreeMap::new();
    let mut actual: BTreeMap<(&str, &str, u64), u64> = BTreeMap::new();
    for task in a(&g["jobs"]) {
        if task["kind"] == "compute" {
            let d = &task["tile_extents"];
            let bytes = mul(4, mul(n(&d["M"]), n(&d["N"]))?)?;
            let key = (t(&task["op_id"]), t(&task["accumulator_buffer_id"]), bytes);
            let count = expected.entry(key).or_default();
            *count = add(*count, 2)?;
        } else if task["kind"] == "local_transfer" && task["purpose"] == "partial" {
            let src = &task["source"];
            let dst = &task["destination"];
            let sb = buffers[t(&src["buffer_id"])];
            let db = buffers[t(&dst["buffer_id"])];
            require(
                n(&src["offset_bytes"]) == 0
                    && n(&dst["offset_bytes"]) == 0
                    && src["size_bytes"] == dst["size_bytes"]
                    && sb["space"] == "vmem"
                    && db["space"] == "vmem"
                    && sb["dtype"] == db["dtype"]
                    && matches!(t(&sb["dtype"]), "fp32" | "int32"),
                "InvalidTransfer",
                "typed accumulator traffic",
            )?;
            let key = (
                t(&task["op_id"]),
                t(&src["buffer_id"]),
                n(&src["size_bytes"]),
            );
            let count = actual.entry(key).or_default();
            *count = add(*count, 1)?;
        }
    }
    require(
        actual == expected,
        "InvalidTransfer",
        "mandatory accumulator traffic",
    )?;
    for op in a(&b["source"]["ops"]) {
        let kind = t(&op["spec"]["operator"]);
        let d = dimensions(op);
        let tasks: Vec<_> = a(&g["jobs"])
            .iter()
            .filter(|j| j["op_id"] == op["id"])
            .collect();
        if kind == "rotary_embedding" {
            let reads: Vec<_> = tasks
                .iter()
                .filter(|j| {
                    j["kind"] == "dma"
                        && buffers[t(&j["source"]["buffer_id"])]["operand"] == "coefficients"
                })
                .collect();
            require(
                reads.len() == 1
                    && n(&reads[0]["payload_bytes"]) == mul(mul(n(&d["S"]), n(&d["R"]))?, 4)?
                    && n(&reads[0]["source"]["offset_bytes"])
                        == mul(mul(n(&b["source"]["context_before"]), n(&d["R"]))?, 4)?,
                "InvalidTransfer",
                "rotary coefficient row",
            )?;
        }
        if !matches!(kind, "paged_gather" | "kv_write" | "attention_fused") {
            continue;
        }
        let (p, tokens, heads, depth) = (n(&d["P"]), n(&d["T"]), n(&d["H"]), n(&d["D"]));
        let pages = tokens.div_ceil(p);
        let append = kind == "kv_write";
        let first = if append {
            n(&b["source"]["context_before"])
        } else {
            0
        };
        let mut expected = vec![];
        for batch in 0..n(&d["B"]) {
            let order: Vec<_> = if kind == "attention_fused" {
                (0..heads)
                    .flat_map(|h| (0..pages).map(move |pg| (pg, h)))
                    .collect()
            } else {
                (first / p..pages)
                    .flat_map(|pg| (0..heads).map(move |h| (pg, h)))
                    .collect()
            };
            for (page, head) in order {
                let lo = first.max(page * p);
                let hi = tokens.min((page + 1) * p);
                let physical = n(&b["source"]["page_indices"][page as usize]);
                expected.push((
                    ((batch * pages + physical) * p * heads + head * p + lo % p) * depth * 2,
                    (hi - lo) * depth * 2,
                ));
            }
        }
        let mut grouped: BTreeMap<&str, Vec<(u64, u64)>> = BTreeMap::new();
        for task in &tasks {
            if task["kind"] != "dma" {
                continue;
            }
            let end = if append { "destination" } else { "source" };
            let buffer = buffers[t(&task[end]["buffer_id"])];
            if buffer["layout"] != "paged" {
                continue;
            }
            let spans = a(&task["spans"]);
            require(spans.len() == 1, "InvalidTransfer", "page slice")?;
            grouped.entry(t(&buffer["id"])).or_default().push((
                n(&spans[0][format!("{end}_offset_bytes")]),
                n(&task["payload_bytes"]),
            ));
        }
        require(
            grouped.len() == 2 && grouped.values().all(|x| x == &expected),
            "InvalidTransfer",
            "page order and valid tail",
        )?;
        let controls: Vec<_> = tasks.iter().filter(|j| j["kind"] == "control").collect();
        require(
            controls.len() == 1
                && controls[0]["page_entries"] == b["source"]["page_indices"]
                && n(&controls[0]["instructions"]) == pages,
            "InvalidCoverage",
            "page lookup",
        )?;
        let indices: Vec<_> = tasks
            .iter()
            .filter(|j| {
                j["kind"] == "dma" && buffers[t(&j["source"]["buffer_id"])]["operand"] == "indices"
            })
            .collect();
        require(
            indices.len() == 1 && n(&indices[0]["payload_bytes"]) == pages * 4,
            "InvalidTransfer",
            "index payload",
        )?;
        let metadata: Vec<_> = buffers
            .values()
            .filter(|x| x["persistent"] == true && x["op_id"] == op["id"])
            .collect();
        require(
            metadata.len() == 1
                && n(&metadata[0]["size_bytes"]) == pages * 4
                && metadata[0]["producer_id"] == controls[0]["id"]
                && a(&g["dependencies"])
                    .iter()
                    .any(|e| e["before"] == indices[0]["id"] && e["after"] == controls[0]["id"]),
            "InvalidCoverage",
            "metadata producer",
        )?;
    }
    Ok(())
}

fn operator_inputs(source: &Value, op: &Value) -> Result<()> {
    let kind = t(&op["spec"]["operator"]);
    let d = dimensions(op);
    let dots = matches!(
        kind,
        "q_projection"
            | "k_projection"
            | "v_projection"
            | "output_projection"
            | "ffn_up"
            | "ffn_gate"
            | "ffn_down"
    );
    if !dots {
        let names: &[&str] = match kind {
            "normalization" | "residual_addition" | "activation" | "scalar_add" => &["X", "W", "Y"],
            "attention_fused" => &["Q", "K", "V", "O"],
            "kv_write" => &["K", "V", "K_cache", "V_cache"],
            "paged_gather" => &["K", "V", "K_out", "V_out"],
            _ => &["X", "Y"],
        };
        let operands = op["spec"]["operands"].as_object().unwrap();
        require(
            operands.keys().map(String::as_str).collect::<BTreeSet<_>>()
                == names.iter().copied().collect(),
            "InvalidCoverage",
            "operator operands",
        )?;
        for (name, operand) in operands {
            let dtype = if kind == "scalar_add" || (kind == "stream_read_sum" && name == "Y") {
                "fp32"
            } else {
                "bf16"
            };
            require(
                operand["dtype"] == dtype,
                "UnsupportedPrecision",
                "operator operand type",
            )?;
        }
    }
    if matches!(kind, "attention_fused" | "kv_write") {
        require(
            n(&d["Hq"]).is_multiple_of(n(&d["H"]))
                && n(&d["D"]) <= 128
                && (n(&d["S"]) == 1 || d["S"] == d["T"])
                && source["context_after"] == d["T"]
                && n(&source["context_after"]).checked_sub(n(&source["context_before"]))
                    == Some(n(&d["S"])),
            "InvalidCoverage",
            "attention/context join",
        )?;
    }
    if source["scope"] == "decoder" {
        let att = a(&source["ops"])
            .iter()
            .find(|o| o["spec"]["operator"] == "attention_fused")
            .ok_or_else(|| refuse("MissingCoverage", "", "decoder attention"))?;
        let ad = dimensions(att);
        require(
            (n(&ad["Hq"]), n(&ad["H"]), n(&ad["D"]), n(&ad["P"])) == (32, 8, 128, 16),
            "UnsupportedShape",
            "decoder architecture",
        )?;
        let m = mul(n(&ad["B"]), n(&ad["S"]))?;
        if dots {
            let k = if kind == "ffn_down" { 14336 } else { 4096 };
            let nn = if matches!(kind, "k_projection" | "v_projection") {
                1024
            } else if matches!(kind, "ffn_up" | "ffn_gate") {
                14336
            } else {
                4096
            };
            require(
                *d == json!({"M":m,"K":k,"N":nn}),
                "InvalidCoverage",
                "decoder projection shape",
            )?;
        } else if matches!(kind, "normalization" | "residual_addition" | "activation") {
            let depth = if kind == "activation" { 14336 } else { 4096 };
            require(
                *d == json!({"M":m,"D":depth}),
                "InvalidCoverage",
                "decoder vector shape",
            )?;
        } else if kind == "kv_write" {
            require(d == ad, "InvalidCoverage", "decoder cache shape")?;
        }
    }
    Ok(())
}
