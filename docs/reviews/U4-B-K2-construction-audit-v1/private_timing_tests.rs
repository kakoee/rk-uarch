//! B literal comparisons at private library API, not public DTO/result execution.
use crate::{Action, Delay, Error, Job, Kind, Simulation};
use serde_json::{Value, json};
#[test]
fn b_133_private_literal_cases() {
    let rows: Value = serde_json::from_str(include_str!("../testdata/b-private-timing.json")).unwrap();
    assert_eq!(rows.as_array().unwrap().len(), 133);
    let mut failures = Vec::new();
    for c in rows.as_array().unwrap() {
        let result = std::panic::catch_unwind(|| check(c));
        if result.is_err() { failures.push(c["case"].clone()); }
    }
    assert!(failures.is_empty(), "B literal mismatches {failures:?}");
}
fn check(c: &Value) {
    let names: Vec<_> = c["jobs"].as_array().unwrap().iter().map(|j|j["id"].as_str().unwrap()).collect();
    let owners: Vec<_> = c["owners"].as_array().unwrap().iter().map(|x|x.as_u64().unwrap()).collect();
    let mut releases = Vec::new();
    let jobs = c["jobs"].as_array().unwrap().iter().enumerate().map(|(i,j)| {
        let clock = c["clocks"].as_array().unwrap().iter().find(|s|s["job_id"]==j["id"]);
        let duration = if let Some(s)=clock {
            releases.push((i as u32,s["start_ps"].as_u64().unwrap()));
            Delay::Cycles { domain:0,n_cycles:s["n_cycles"].as_u64().unwrap() }
        } else { Delay::Picoseconds(j["duration_ps"].as_u64().unwrap()) };
        let dependencies=c["dependencies"].as_array().unwrap().iter().filter(|d|d["after"]==j["id"]).map(|d|names.iter().position(|n|*n==d["before"].as_str().unwrap()).unwrap() as u32).collect();
        Job {id:i as u32,owner:owners.iter().position(|o|*o==j["owner_id"].as_u64().unwrap()).unwrap() as u32,duration,dependencies}
    }).collect();
    let result=Simulation::with_releases(vec![c["freq"].as_u64().unwrap()],owners.len(),jobs,releases).and_then(Simulation::run);
    let a=&c["answer"];
    if a["outcome"]=="TimeOverflow" { assert!(matches!(result,Err(Error::TimeOverflow)),"{}: expected actual overflow",c["case"]);return; }
    let out=result.unwrap();assert_eq!(out.duration_ps,a["duration_ps"].as_u64().unwrap(),"{} duration",c["case"]);
    assert_eq!(out.completed_jobs,names.len() as u64);
    let intervals:Vec<_>=out.jobs.iter().map(|j|json!([names[j.job_id as usize],owners[j.owner as usize],j.ready_ps,j.start_ps,j.end_ps])).collect();
    assert_eq!(json!(intervals),a["intervals"],"{} intervals",c["case"]);
    let dispatch:Vec<_>=out.records.iter().filter(|r|r.action==Action::Dispatch).collect();
    if let Some(events)=a.get("event_projection") {
        let rows:Vec<_>=dispatch.iter().map(|r| {
            let kind=if r.event_kind==Kind::TaskReady as u16 {"TASK_READY"} else if r.event_kind==Kind::TaskRelease as u16 {"TASK_RELEASE"} else if r.event_kind==Kind::DependencyReady as u16 {"DEPENDENCY_READY"} else if r.event_kind==Kind::OwnerGrant as u16 {"OWNER_GRANT"} else if r.event_kind==Kind::ComputeDone as u16 {"COMPUTE_DONE"} else {panic!("foreign kind")};
            json!([r.t_ps,r.phase,names[r.job_id as usize],kind])
        }).collect();
        assert_eq!(json!(rows),*events,"{} phases",c["case"]);
    }
    for (o,id) in owners.iter().enumerate() {
        let busy:u64=out.jobs.iter().filter(|j|j.owner as usize==o).map(|j|j.end_ps-j.start_ps).sum();
        assert_eq!(busy,a["busy_by_owner"][id.to_string()].as_u64().unwrap());
    }
    if let Some(causes)=a.get("chosen_predecessors") {
        for (name,want) in causes.as_object().unwrap() {
            let index=names.iter().position(|n|n==name).unwrap();let j=&out.jobs[index];
            let grant=dispatch.iter().position(|r|r.job_id as usize==index && r.event_kind==Kind::OwnerGrant as u16).unwrap();
            let actual=j.dependency_resource_predecessors.iter().filter(|p|out.jobs[**p as usize].end_ps==j.start_ps && dispatch.iter().position(|r|r.job_id==**p && r.event_kind==Kind::ComputeDone as u16).unwrap()<grant).min().map(|p|names[*p as usize]);
            assert_eq!(json!(actual),*want,"{} cause {}",c["case"],name);
        }
    }
}
