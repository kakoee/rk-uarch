//! Projection of completed native state. No expected row or declared-work fallback.
use crate::{
    carrier::{Result, refuse},
    component::{Activity, Counts, Runtime, add, mul},
    component_admission::{Admitted, TaskKind},
    hardware,
};
use serde_json::{Value, json};
use std::collections::{BTreeMap, BTreeSet};
fn observed(v: Vec<Value>) -> Value {
    json!({"status":"observed","records":v})
}
fn aid(a: usize) -> String {
    format!("activity-{a:08}")
}
fn domain(a: &Activity) -> Option<&'static str> {
    a.phase.domain.map(|d| ["core", "noc", "dram"][d])
}
fn totals(c: &Counts) -> Result<(Value, Value, Value, Value)> {
    Ok((
        json!({"matrix_ops":mul(2,c.mac)? as f64,"vector_ops":0.0,"memory_read_bytes":c.read as f64,"memory_write_bytes":c.write as f64}),
        json!({"sram_read_bytes":c.sram_read as f64,"sram_write_bytes":c.sram_write as f64,"noc_flit_hop_count":null}),
        json!({"format":"uarch-native-work-counts/1","completed_mac_count":c.mac,"issued_matrix_ops":c.issued,"vector_arithmetic_ops":0,"cast_ops":0}),
        json!({"format":"uarch-native-traffic-counts/1","read_payload_bytes":c.read,"write_payload_bytes":c.write,"read_transaction_bytes":c.read_txn,"write_transaction_bytes":c.write_txn,"unicast_payload_bytes":c.unicast}),
    ))
}
fn kinds(a: &Activity) -> (&'static str, &'static str) {
    if a.alignment {
        return ("TASK_READY", "DEPENDENCY_READY");
    }
    match a.phase.name {
        "compute_overhead" | "compute_stage" | "compute_wave" | "compute_drain" => {
            ("OWNER_GRANT", "COMPUTE_DONE")
        }
        "read_port" => ("OWNER_GRANT", "DMA_DONE"),
        "write_port" => ("OWNER_GRANT", "MEM_RESP"),
        "channel_service" | "dram_latency" => ("MEM_REQ", "MEM_RESP"),
        "request_noc" | "response_noc" | "unicast_noc" => ("NOC_HEAD", "NOC_TAIL"),
        "ack" => ("TASK_READY", "DMA_DONE"),
        "barrier" => ("SYNC_ARRIVE", "BARRIER_RELEASE"),
        _ => unreachable!("typed phase"),
    }
}
fn union(mut spans: Vec<(u64, u64)>) -> Result<u64> {
    spans.sort();
    let (mut end, mut total) = (0, 0);
    for (a, b) in spans {
        if b > end {
            total = add(total, b - a.max(end))?;
            end = b;
        }
    }
    Ok(total)
}
pub(crate) fn construct(v: &Admitted, r: &Runtime) -> Result<Value> {
    let mut events = vec![];
    let mut acts = vec![];
    let mut clocks = vec![];
    let mut resources = vec![];
    let mut queues = vec![];
    let mut jobs = vec![];
    let mut dma = vec![];
    let mut transfers = vec![];
    let mut allocations = vec![];
    for (i, e) in r.events.iter().enumerate() {
        let a = &r.activities[e.activity];
        let kind = kinds(a);
        events.push(json!({"event_seq":e.seq,"observation_ordinal":i,"t_ps":e.time,"phase":e.phase,"target_id":a.phase.owner,"kind":if e.completion{kind.1}else{kind.0},"job_id":v.graph.jobs[a.job].id}));
    }
    for (i, a) in r.activities.iter().enumerate() {
        let task = &v.graph.jobs[a.job];
        let s = &r.sequences[a.sequence];
        let id = aid(i);
        let occupied = !a.alignment && a.phase.occupies;
        if (a.start > 0 && a.causes.is_empty())
            || a.causes.iter().any(|(p, _)| {
                *p >= i
                    || r.activities[*p].end != a.start
                    || r.activities[*p].completion > a.dispatch
            })
        {
            return Err(refuse(
                "IncompleteObservations",
                "",
                "activity requires actual tight earlier cause",
            ));
        }
        let mut predecessors: Vec<_> = a
            .causes
            .iter()
            .map(|(p, relation)| json!({"activity_id":aid(*p),"relation":relation}))
            .collect();
        predecessors.sort_by(|a, b| {
            a["activity_id"]
                .as_str()
                .cmp(&b["activity_id"].as_str())
                .then(a["relation"].as_str().cmp(&b["relation"].as_str()))
        });
        acts.push(json!({"activity_id":id,"job_id":task.id,"request_id":s.request,"subphase":a.phase.name,"kind":if a.alignment{"alignment"}else{"service"},"ready_ps":a.ready,"start_ps":a.start,"end_ps":a.end,"owner_id":a.phase.owner,"category":a.phase.category,"receiving_domain":domain(a),"occupies_resource":occupied,"dispatch_ordinal":a.dispatch,"completion_ordinal":a.completion,"predecessors":predecessors}));
        if occupied {
            let ratio = |end: bool| -> Value {
                a.ratio
                    .map(|(lo, hi)| {
                        let x = if end { hi } else { lo };
                        json!({"numerator":x.n,"denominator":x.d})
                    })
                    .unwrap_or(Value::Null)
            };
            resources.push(json!({"owner_id":a.phase.owner,"job_id":task.id,"start_ps":a.start,"end_ps":a.end,"activity":a.phase.name,"limiting_resource_id":a.phase.owner,"service_start_ps_ratio":ratio(false),"service_end_ps_ratio":ratio(true),"activity_id":id}));
        }
        let clocked =
            a.phase.domain.is_some() && !(a.phase.name.ends_with("_noc") && !a.phase.occupies);
        if clocked {
            let aligned = a.clock_aligned.ok_or_else(|| {
                refuse(
                    "IncompleteObservations",
                    "",
                    "missing executed alignment outcome",
                )
            })?;
            clocks.push(json!({"job_id":task.id,"domain":domain(a),"grant_ps":a.start,"n_cycles":if a.alignment{0}else{a.phase.cycles},"raw_edge_outcome":"success","aligned_start_ps":aligned,"completion_ps":a.end,"activity_id":id}));
        }
        if a.phase.domain.is_some() {
            for (population, begin, end) in
                [("waiting", a.ready, a.start), ("service", a.start, a.end)]
            {
                queues.push(json!({"queue_id":format!("activity:{}:{}",a.phase.name,a.phase.owner),"item_id":s.request.as_ref().unwrap_or(&task.id),"population":population,"enter_ps":begin,"leave_ps":end,"owner_id":a.phase.owner,"clock_domain":domain(a),"activity_id":id}));
            }
        }
        if a.phase.name == "channel_service" {
            let resource = v
                .owners
                .iter()
                .find(|(_, owner)| **owner == a.phase.owner)
                .expect("admitted owner")
                .0;
            let channel = resource.strip_prefix("channel:").expect("channel owner");
            for (population, begin, end) in
                [("waiting", a.ready, a.start), ("service", a.start, a.end)]
            {
                queues.push(json!({"queue_id":format!("channel_service:{channel}"),"item_id":s.request,"population":population,"enter_ps":begin,"leave_ps":end,"owner_id":a.phase.owner,"clock_domain":null,"activity_id":null}));
            }
        }
    }
    for (i, t) in v.graph.jobs.iter().enumerate() {
        let j = &r.jobs[i];
        let compute = matches!(t.kind, TaskKind::Compute { .. });
        jobs.push(json!({"job_id":t.id,"op_id":t.op_id,"group_id":if compute{t.raw["group_id"].clone()}else{Value::Null},"repeat_index":if compute{t.raw["repeat_index"].clone()}else{Value::Null},"tile_origin":if compute{t.raw["tile_origin"].clone()}else{Value::Null},"tile_extents":if compute{t.raw["tile_extents"].clone()}else{Value::Null},"release_ps":0,"ready_ps":j.ready,"start_ps":j.start,"end_ps":j.end,"owner_id":t.owner,"blocking_predecessor_ids":[],"useful_matrix_ops":j.useful,"issued_matrix_ops":j.issued,"vector_arithmetic_ops":0,"cast_ops":0}));
    }
    for s in &r.sequences {
        let Some(req) = &s.request else { continue };
        let task = &v.graph.jobs[s.job];
        let direction = if s.engine.is_none() {
            "unicast"
        } else if s.write {
            "write"
        } else {
            "read"
        };
        let route = &task.raw;
        if s.end.is_none() {
            return Err(refuse("IncompleteExecution", "", "uncompleted request"));
        }
        let route_id = if s.engine.is_none() {
            route["route_id"].clone()
        } else {
            route["fragments"]
                .as_array()
                .unwrap()
                .iter()
                .find(|f| f["request_id"] == req.as_str())
                .unwrap()["route_id"]
                .clone()
        };
        dma.push(json!({"request_id":req,"job_id":task.id,"dma_engine_id":s.engine,"direction":direction,"source_buffer_id":s.source,"destination_buffer_id":s.destination,"payload_bytes":s.payload,"transaction_bytes":if s.engine.is_some(){256}else{0},"credit_acquire_ps":if s.engine.is_some(){s.issue}else{None},"issue_ps":s.issue,"complete_ps":s.end,"credit_release_ps":if s.engine.is_some(){s.end}else{None},"route_id":route_id}));
        if let Some(engine) = s.engine {
            queues.push(json!({"queue_id":format!("dma_inflight:{engine}"),"item_id":req,"population":"inflight","enter_ps":s.issue,"leave_ps":s.end,"owner_id":task.owner,"clock_domain":null,"activity_id":null}));
        }
        let boundaries = if s.engine.is_none() {
            vec![("unicast_noc", vec!["unicast_noc"], s.payload, 0)]
        } else {
            vec![
                (
                    "request_noc",
                    vec!["request_noc"],
                    if s.write { s.payload } else { 0 },
                    0,
                ),
                (
                    "dram",
                    vec!["dram_latency", "channel_service"],
                    s.payload,
                    256,
                ),
                (
                    "response_noc",
                    vec!["response_noc"],
                    if s.write { 0 } else { s.payload },
                    0,
                ),
                (
                    "core_port",
                    vec![if s.write { "write_port" } else { "read_port" }],
                    s.payload,
                    0,
                ),
            ]
        };
        for (boundary, phases, payload, txn) in boundaries {
            let first = s
                .activities
                .iter()
                .map(|&a| &r.activities[a])
                .find(|a| a.phase.name == phases[0])
                .unwrap();
            let last = s
                .activities
                .iter()
                .map(|&a| &r.activities[a])
                .rev()
                .find(|a| a.phase.name == *phases.last().unwrap())
                .unwrap();
            transfers.push(json!({"request_id":req,"boundary_id":boundary,"direction":direction,"payload_bytes":payload,"transaction_bytes":txn,"enter_ps":first.ready,"leave_ps":last.end}));
        }
    }
    for (i, b) in v.graph.buffers.iter().enumerate() {
        let state = &r.allocations[i];
        let raw = v.raw["mapped_point"]["task_graph"]["buffers"]
            .as_array()
            .unwrap()
            .iter()
            .find(|x| x["id"] == b.id)
            .unwrap();
        if state.start.is_none() {
            return Err(refuse(
                "IncompleteObservations",
                "",
                "buffer was never allocated",
            ));
        }
        allocations.push(json!({"buffer_id":b.id,"space":b.space,"owner_id":b.owner,"offset_bytes":b.offset,"size_bytes":b.size,"allocate_ps":state.start,"free_ps":state.end,"initially_live":raw["initial_residency"]=="preloaded","last_consumer_ids":b.consumers.iter().map(|&j|v.graph.jobs[j].id.clone()).collect::<Vec<_>>()}));
    }
    let tie = |i: usize| {
        let a = &r.activities[i];
        (
            a.phase.owner,
            v.graph.jobs[a.job].id.clone(),
            r.sequences[a.sequence].request.clone().unwrap_or_default(),
            a.phase.name,
            aid(i),
        )
    };
    let mut cursor = r
        .activities
        .iter()
        .enumerate()
        .filter(|(_, a)| a.end == r.duration)
        .map(|(i, _)| i)
        .min_by_key(|&i| tie(i))
        .ok_or_else(|| refuse("IncompleteExecution", "", "no terminal activity"))?;
    let mut seen = BTreeSet::new();
    let mut chain = vec![];
    loop {
        if !seen.insert(cursor) {
            return Err(refuse(
                "IncompleteObservations",
                "",
                "causal activity cycle",
            ));
        }
        let a = &r.activities[cursor];
        if a.end > a.start {
            chain.push(cursor)
        }
        if let Some((p, _)) = a.causes.iter().min_by_key(|(p, _)| tie(*p)) {
            cursor = *p;
        } else {
            if a.start != 0 {
                return Err(refuse("IncompleteObservations", "", "causal gap"));
            }
            break;
        }
    }
    chain.reverse();
    let mut critical = vec![];
    let mut attribution = BTreeMap::from([
        ("compute", 0u64),
        ("memory", 0),
        ("noc", 0),
        ("sync", 0),
        ("overhead", 0),
    ]);
    let mut t = 0;
    for i in chain {
        let a = &r.activities[i];
        if a.start != t {
            return Err(refuse(
                "IncompleteObservations",
                "",
                "critical partition gap",
            ));
        }
        t = a.end;
        let total = attribution.get_mut(a.phase.category).unwrap();
        *total = add(*total, a.end - a.start)?;
        critical.push(json!({"kind":"service","start_ps":a.start,"end_ps":a.end,"cause_job_id":v.graph.jobs[a.job].id,"predecessor_id":null,"limiting_resource_id":a.phase.owner,"category":a.phase.category,"activity_id":aid(i)}));
    }
    let mut busy = vec![];
    for &owner in v.owners.values() {
        let spans = r
            .activities
            .iter()
            .filter(|a| !a.alignment && a.phase.occupies && a.phase.owner == owner)
            .map(|a| (a.start, a.end))
            .collect();
        busy.push(json!({"owner_id":owner,"busy_time_ps":union(spans)?}));
    }
    busy.sort_by_key(|x| x["owner_id"].as_u64().unwrap());
    let mut per_op: BTreeMap<String, Counts> = BTreeMap::new();
    for (i, t) in v.graph.jobs.iter().enumerate() {
        if let Some(op) = &t.op_id {
            per_op.entry(op.clone()).or_default().merge(&r.per_job[i])?;
        }
    }
    let mut op_rows = vec![];
    for (op, c) in per_op {
        if !v
            .graph
            .jobs
            .iter()
            .any(|t| t.op_id.as_ref() == Some(&op) && matches!(t.kind, TaskKind::Compute { .. }))
        {
            continue;
        }
        let (counts, ext, work, traffic) = totals(&c)?;
        op_rows.push(json!({"op_id":op,"counts":counts,"ext_counts":ext,"work_counts":work,"traffic_counts":traffic}));
    }
    let (counts, ext, work, traffic) = totals(&r.counts)?;
    dma.sort_by(|a, b| a["request_id"].as_str().cmp(&b["request_id"].as_str()));
    let observations = json!({"format":"uarch-native-observations/2","events":observed(events),"jobs":observed(jobs),"activities":observed(acts),"clocks":observed(clocks),"dma":observed(dma),"transfers":observed(transfers),"allocations":observed(allocations),"queue_membership":observed(queues),"resource_intervals":observed(resources),"critical_path":observed(critical)});
    let mut result = json!({"protocol":"uarch-engine/3","job_hash":v.raw["job_hash"],"engine":v.raw["engine"],"scope":v.raw["workload_closure"]["scope"]["kind"],"completion":"complete","duration_ps":r.duration,"completed_jobs":v.graph.jobs.iter().enumerate().filter(|(i,_)|r.jobs[*i].end.is_some()).map(|(_,t)|t.id.clone()).collect::<Vec<_>>(),"admission":v.raw["admission"],"counts":counts,"ext_counts":ext,"work_counts":work,"traffic_counts":traffic,"per_op":op_rows,"busy_time_ps":busy,"attribution_ps":attribution,"diagnostics":{"matrix_util_ratio":null,"vector_util_ratio":null,"dma_compute_overlap_ratio":null,"sram_bank_conflict_stall_ratio":null,"noc_latency_p50_ps":null,"noc_latency_p99_ps":null,"noc_max_link_util_ratio":null,"dram_bw_util_ratio":null,"dram_row_hit_ratio":null,"energy_pj":null},"fidelity_detail":v.raw["fidelity_detail"],"unrepresented":["diagnostics/dram_row_hit_ratio","diagnostics/energy_pj","diagnostics/noc_max_link_util_ratio","diagnostics/sram_bank_conflict_stall_ratio","diagnostics/vector_util_ratio","ext_counts/noc_flit_hop_count","u_c0_duration_ps"],"simulator_metrics":{"event_count":r.events.len(),"completed_job_count":r.jobs.iter().filter(|j|j.end.is_some()).count(),"max_live_events":r.max_live_events},"trace_hash":null,"u_c0_duration_ps":null,"observations":observations,"owners":v.raw["owners"]});
    result["result_hash"] = Value::String(hardware::digest(&result)?);
    Ok(result)
}
