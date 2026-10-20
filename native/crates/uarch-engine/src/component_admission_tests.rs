//! PRIVATE SYNTHETIC admission only. Tests never dispatch or establish host authority.
use crate::{
    component_admission::{self, TaskKind},
    hardware, wire,
};
use serde_json::{Value, json};
use std::collections::BTreeSet;
fn fixture(id: &str) -> Value {
    let v: Value =
        serde_json::from_str(include_str!("../testdata/synthetic-component-jobs.json")).unwrap();
    v[id].clone()
}

fn seal(v: &mut Value, key: &str) {
    v.as_object_mut().unwrap().remove(key);
    v[key] = json!(hardware::digest(v).unwrap());
}
fn reseal(v: &mut Value) {
    for p in v["workload_closure"]["points"].as_array_mut().unwrap() {
        seal(&mut p["task_graph"], "graph_hash");
        seal(p, "payload_hash");
    }
    v["mapped_point"] = v["workload_closure"]["points"][0].clone();
    v["point_hash"] = v["mapped_point"]["payload_hash"].clone();
    v["profile"]["entries"][0]["graph_hash"] =
        v["mapped_point"]["task_graph"]["graph_hash"].clone();
    v["profile"]["entries"][0]["point_hash"] = v["point_hash"].clone();
    seal(&mut v["profile"], "profile_hash");
    v["admission"]["profile_hash"] = v["profile"]["profile_hash"].clone();
    v["workload_closure"]["admission"] = v["admission"].clone();
    seal(&mut v["workload_closure"], "bundle_hash");
    v["bundle_hash"] = v["workload_closure"]["bundle_hash"].clone();
    seal(v, "job_hash");
}
fn check(v: &Value) -> crate::carrier::Result<component_admission::Admitted> {
    component_admission::validate(&wire::canonical(v).unwrap())
}
fn refusal(v: &Value, code: &str) {
    assert_eq!(check(v).unwrap_err().code, code);
}
#[test]
fn synthetic_typed_admission_literals() {
    let a = check(&fixture("C02")).unwrap();
    assert_eq!(a.graph.jobs.len(), 1);
    assert!(matches!(
        a.graph.jobs[0].kind,
        TaskKind::Compute {
            core: 0,
            m: 3,
            k: 5,
            n: 7
        }
    ));
    assert_eq!(a.hardware.freq, [1_000_000_000; 3]);
    assert_eq!(
        (a.hardware.channel_step_num, a.hardware.channel_step_den),
        (159744, 71)
    );
}
#[test]
fn synthetic_positive_inventory_is_nonempty() {
    let v: Value =
        serde_json::from_str(include_str!("../testdata/synthetic-component-jobs.json")).unwrap();
    assert_eq!(v.as_object().unwrap().len(), 79);
    let mut admitted = 0;
    for (id, j) in v.as_object().unwrap() {
        if id == "D13-barrier" {
            refusal(j, "InvalidResource");
        } else {
            check(j).unwrap_or_else(|e| panic!("{id}: {e:?}"));
            admitted += 1;
        }
    }
    assert_eq!(admitted, 78);
}
#[test]
fn synthetic_stale_closure_refuses() {
    let mut v = fixture("C02");
    v["workload_closure"]["points"][0]["point_id"] = json!("changed");
    refusal(&v, "ContentHashMismatch");
}
#[test]
fn synthetic_full_point_resource_validation() {
    let mut v = fixture("C02");
    let mut p = v["workload_closure"]["points"][0].clone();
    p["point_id"] = json!("zz-unselected");
    p["task_graph"]["buffers"][0]["size_bytes"] = json!(999999999);
    v["workload_closure"]["points"]
        .as_array_mut()
        .unwrap()
        .push(p);
    reseal(&mut v);
    refusal(&v, "CapacityExceeded");
}
#[test]
fn synthetic_operand_access_precondition() {
    let mut v = fixture("C02");
    v["workload_closure"]["scope"]["ops"][0]["operand_access"]
        .as_object_mut()
        .unwrap()
        .remove("X");
    reseal(&mut v);
    refusal(&v, "InvalidCoverage");
}

#[test]
fn synthetic_terminal_reader_and_capacity() {
    let mut v = fixture("C02");
    let buffers = v["workload_closure"]["points"][0]["task_graph"]["buffers"]
        .as_array_mut()
        .unwrap();
    let sx = buffers.iter_mut().find(|b| b["id"] == "sx").unwrap();
    sx["final_consumer_ids"] = json!([]);
    reseal(&mut v);
    refusal(&v, "InvalidDependency");
    let mut v = fixture("C02");
    v["workload_closure"]["points"][0]["task_graph"]["buffers"][0]["size_bytes"] = json!(1);
    reseal(&mut v);
    refusal(&v, "CapacityExceeded");
}
#[test]
fn synthetic_schema_rejects_unknown_field() {
    let mut v = fixture("C02");
    v["prevalidated"] = json!(true);
    refusal(&v, "InvalidCarrier");
}
#[test]
fn synthetic_policy_two_lifetime_inventory() {
    let inputs: Value = serde_json::from_str(include_str!(
        "../testdata/synthetic-component-admission-jobs.json"
    ))
    .unwrap();
    assert_eq!(inputs.as_object().unwrap().len(), 7);
    let mut successes = 0;
    let mut refused = 0;
    for (id, item) in inputs.as_object().unwrap() {
        let got = check(&item["job"]);
        if item["expected"] == "success" {
            let a = got.unwrap_or_else(|e| panic!("{id}: {e:?}"));
            assert!(
                a.graph
                    .buffers
                    .iter()
                    .any(|b| b.space == "accumulator" && !b.persistent)
            );
            successes += 1;
        } else {
            assert_eq!(
                got.unwrap_err().code,
                item["expected"].as_str().unwrap(),
                "{id}"
            );
            refused += 1;
        }
    }
    assert_eq!((successes, refused), (3, 4));
}
#[test]
fn synthetic_true_producer_precedes_terminal_checks() {
    let inputs: Value = serde_json::from_str(include_str!(
        "../testdata/synthetic-component-admission-jobs.json"
    ))
    .unwrap();
    let mut v = inputs["B3-writer-control"]["job"].clone();
    let graph = &mut v["workload_closure"]["points"][0]["task_graph"];
    let jobs = graph["jobs"].clone();
    let buffers = graph["buffers"].as_array_mut().unwrap();
    let acc = buffers
        .iter_mut()
        .find(|b| b["space"] == "accumulator" && !b["producer_id"].is_null())
        .unwrap();
    let other = jobs
        .as_array()
        .unwrap()
        .iter()
        .find(|j| j["kind"] == "compute" && j["accumulator_buffer_id"] != acc["id"])
        .expect("distinct accumulator producer control");
    acc["producer_id"] = other["id"].clone();
    acc["final_consumer_ids"] = json!([]);
    reseal(&mut v);
    refusal(&v, "InvalidDependency");
}
fn truncate_transfer(v: &mut Value, direction: &str) {
    let g = &mut v["workload_closure"]["points"][0]["task_graph"];
    let j = g["jobs"]
        .as_array_mut()
        .unwrap()
        .iter_mut()
        .find(|j| {
            j["kind"] == "dma"
                && j["direction"] == direction
                && j["fragments"].as_array().unwrap().last().unwrap()["payload_bytes"]
                    .as_u64()
                    .unwrap()
                    > 1
        })
        .unwrap();
    for k in ["source", "destination"] {
        let size = j[k]["size_bytes"].as_u64().unwrap();
        j[k]["size_bytes"] = json!(size - 1);
    }
    let f = j["fragments"].as_array_mut().unwrap().last_mut().unwrap();
    f["payload_bytes"] = json!(f["payload_bytes"].as_u64().unwrap() - 1);
    reseal(v);
}
#[test]
fn synthetic_complete_operand_and_cold_output() {
    let control = fixture("C05-B");
    check(&control).unwrap();
    let mut read = control.clone();
    truncate_transfer(&mut read, "read");
    refusal(&read, "InvalidTransfer");
    let mut write = control;
    truncate_transfer(&mut write, "write");
    refusal(&write, "InvalidTransfer");
}

#[test]
fn synthetic_buffer_end_overflow_refuses_without_panic() {
    let mut v = fixture("C02");
    let b = &mut v["workload_closure"]["points"][0]["task_graph"]["buffers"][0];
    b["offset_bytes"] = json!(u64::MAX - 255);
    b["size_bytes"] = json!(512);
    reseal(&mut v);
    refusal(&v, "CapacityExceeded");
}
#[test]
fn synthetic_transport_allocations_follow_producer() {
    let a = check(&fixture("D01")).unwrap();
    let produced: Vec<_> = a
        .graph
        .buffers
        .iter()
        .filter(|b| b.producer.is_some())
        .collect();
    assert_eq!(produced.len(), 1);
    assert!(!produced[0].persistent);
    let initial: Vec<_> = a
        .graph
        .buffers
        .iter()
        .filter(|b| b.producer.is_none())
        .collect();
    assert_eq!(initial.len(), 1);
    assert!(initial[0].persistent);
}

// PRIVATE SYNTHETIC: /2 request inventory shares DMA fragment and unicast IDs.
#[test]
fn synthetic_request_identity_collision_rejected_before_runtime() {
    let v: Value =
        serde_json::from_str(include_str!("../testdata/synthetic-request-collision.json")).unwrap();
    refusal(&v, "InvalidTransfer");
}
#[test]
fn synthetic_distinct_transport_request_identity_restores_complete_inventory() {
    let mut v: Value =
        serde_json::from_str(include_str!("../testdata/synthetic-request-collision.json")).unwrap();
    let jobs = v["workload_closure"]["points"][0]["task_graph"]["jobs"]
        .as_array_mut()
        .unwrap();
    let dma = jobs.iter_mut().find(|j| j["kind"] == "dma").unwrap();
    dma["fragments"][0]["request_id"] = json!("synthetic-distinct-fragment");
    reseal(&mut v);
    assert_eq!(check(&v).unwrap().graph.jobs.len(), 2);
    let result = crate::component::execute(&wire::canonical(&v).unwrap()).unwrap();
    let rows = result["observations"]["dma"]["records"].as_array().unwrap();
    let ids: BTreeSet<_> = rows
        .iter()
        .map(|x| x["request_id"].as_str().unwrap())
        .collect();
    assert_eq!(rows.len(), 2);
    assert_eq!(rows[0]["request_id"], "r00.00");
    assert_eq!(rows[1]["request_id"], "synthetic-distinct-fragment");
    assert_eq!(
        ids,
        BTreeSet::from(["r00.00", "synthetic-distinct-fragment"])
    );
    assert_eq!(result["completed_jobs"], json!(["r00", "r00.00"]));
}
