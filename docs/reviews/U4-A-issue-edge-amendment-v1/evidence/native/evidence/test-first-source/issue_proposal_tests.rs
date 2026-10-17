//! PRIVATE UNAPPLIED /3 tests. Typed-state probes are not claimed as mapped admission.
use super::*;
use crate::component_admission::Task;
use serde_json::json;
fn anchor(v: &Value) -> Trust {
    Trust { registry: v["registry"]["registry_hash"].as_str().unwrap().into(),
        profiles: BTreeMap::from([(v["profile"]["profile_hash"].as_str().unwrap().into(), BTreeSet::from([v["admission"]["case_id"].as_str().unwrap().into()]))]), engine: v["engine"].clone() }
}
fn fixture(id: &str) -> (Value, Admitted) {
    let all: Value = serde_json::from_str(include_str!("../testdata/synthetic-component-jobs.json")).unwrap();
    let v = all[id].clone();
    let a = component_admission::validate(&crate::wire::canonical(&v).unwrap(), &anchor(&v)).unwrap(); (v,a)
}
fn model_two(v: &mut Value) { v["engine"]["model"]["version"] = json!("2"); v.as_object_mut().unwrap().remove("job_hash"); v["job_hash"] = json!(crate::hardware::digest(v).unwrap()); }
// Direct typed-state synthesis after real baseline admission. No result-carrier claim.
fn boundary(write: bool, ready: u64, cap: u64, independent: bool) -> Admitted {
    let (_,mut a) = fixture(if write {"D02"} else {"D01"});
    a.hardware.freq[1] = 1_000_000_000_000;
    a.hardware.hop_cycles = 2000;
    a.hardware.barrier_cycles = ready;
    a.hardware.credit_limit = cap;
    let mut second = a.graph.jobs[0].clone(); second.id = "second".into();
    if let TaskKind::Dma {engine,source,destination,fragments,..} = &mut second.kind {
        if independent { *engine = 1; second.owner += 1; }
        *source = format!("second-{source}"); *destination = format!("second-{destination}");
        fragments[0].id = "second.0".into();
    }
    let extra: Vec<_> = a.graph.buffers.iter().cloned().map(|mut b| { b.id=format!("second-{}",b.id); b.producer=b.producer.map(|_|1); b.consumers=b.consumers.iter().map(|_|1).collect(); b }).collect();
    a.graph.buffers.extend(extra);
    a.graph.jobs.push(second);
    a.graph.jobs.push(Task { id:"barrier".into(), op_id:None, owner:52, kind:TaskKind::Barrier, raw:json!({}) });
    a.graph.dependencies=vec![(2,1)]; a
}
fn issue_alignment(r: &Runtime, sequence: usize) -> &Activity { r.activities.iter().find(|x| x.sequence==sequence && x.phase.name=="dma_issue" && x.alignment).expect("explicit issue alignment") }
#[test]
fn proposed_raw_gap_has_exact_issue_alignment_and_queues() {
    let mut v:Value=serde_json::from_str(include_str!("../testdata/synthetic-issue-core-gap.json")).unwrap();model_two(&mut v);
    let r=execute_with_observations(&crate::wire::canonical(&v).unwrap(), &anchor(&v),ObservationVersion::V3).unwrap();
    assert_eq!(r["observations"]["format"],"uarch-native-observations/3");
    let rows=r["observations"]["activities"]["records"].as_array().unwrap();
    let align=rows.iter().find(|x| x["subphase"]=="dma_issue" && x["kind"]=="alignment").unwrap();
    assert_eq!((align["ready_ps"].as_u64(),align["start_ps"].as_u64(),align["end_ps"].as_u64()),(Some(26667),Some(26667),Some(27000)));
    assert_eq!(align["occupies_resource"],false);
    let service=rows.iter().find(|x| x["subphase"]=="dma_issue" && x["kind"]=="service").unwrap();
    assert_eq!(service["start_ps"],27000);assert_eq!(service["end_ps"],27000);
    let dma=r["observations"]["dma"]["records"].as_array().unwrap().iter().find(|x| x["direction"]=="read").unwrap();
    assert_eq!(dma["reservation_ps"],26667);assert_eq!(dma["issue_ps"],27000);assert_eq!(dma["credit_acquire_ps"],27000);
    let q=r["observations"]["queue_membership"]["records"].as_array().unwrap();
    let pending=q.iter().find(|x| x["queue_id"]=="dma_pending:0").unwrap();
    assert_eq!(pending["population"],"pending");assert_eq!(pending["enter_ps"],26667);assert_eq!(pending["leave_ps"],27000);
    assert!(pending["clock_domain"].is_null());assert!(pending["activity_id"].is_null());
}
#[test]
fn proposed_model_version_is_explicit_and_legacy_is_unchanged() {
    let (v,_)=fixture("D01");let raw=crate::wire::canonical(&v).unwrap();
    let old=execute(&raw,&anchor(&v)).unwrap();assert_eq!(old["duration_ps"],60000);assert_eq!(old["observations"]["format"],"uarch-native-observations/2");
    assert!(old["observations"]["dma"]["records"][0].get("reservation_ps").is_none());
    assert_eq!(execute_with_observations(&raw,&anchor(&v),ObservationVersion::V3).unwrap_err().code,"UnsupportedFidelity");
}
#[test]
fn proposed_read_write_credit_cause_boundary_is_reservation_time() {
    for write in [false,true] { for ready in [59999,60000,60001] {
        let a=boundary(write,ready,1,false);let r=Runtime::new_version(&a,ObservationVersion::V3).unwrap().run(&a).unwrap();
        assert_eq!(r.sequences[0].end,Some(60000));
        assert_eq!(r.sequences[1].reservation,Some(ready.max(60000)));
        assert_eq!(r.sequences[1].issue,Some(if ready==60001 {61000}else{60000}));
        let align=issue_alignment(&r,1);let relations:BTreeSet<_>=align.causes.iter().map(|x|x.1).collect();
        assert_eq!(relations, BTreeSet::from([if ready==59999 {"credit"}else{"dependency"}]));
        assert_eq!(r.jobs[1].start,r.sequences[1].reservation);
        for (i,b) in a.graph.buffers.iter().enumerate().filter(|(_,b)|b.producer==Some(1)) {assert!(!b.persistent);assert_eq!(r.allocations[i].start,r.jobs[1].start);}
    }}
}
#[test]
fn proposed_cap_two_and_independent_engines_reserve_before_issue() {
    for (cap,independent) in [(2,false),(1,true)] {for write in [false,true] {
        let a=boundary(write,59999,cap,independent);let r=Runtime::new_version(&a,ObservationVersion::V3).unwrap().run(&a).unwrap();
        assert_eq!(r.sequences[1].reservation,Some(59999));assert_eq!(r.sequences[1].issue,Some(60000));
        assert_eq!(issue_alignment(&r,1).causes.iter().map(|x|x.1).collect::<Vec<_>>(),vec!["dependency"]);
    }}
}
#[test]
fn proposed_cap_one_pending_reservation_prevents_double_issue() {
    let mut a=boundary(false,59999,1,false);a.graph.dependencies=vec![(2,0),(2,1)];
    let mut r=Runtime::new_version(&a,ObservationVersion::V3).unwrap();
    // Explicit private scheduler state at dependency completion; inspect before any payload step.
    r.now=59999;r.jobs[2].ready=Some(0);r.jobs[2].end=Some(59999);r.ready_jobs(&a);
    r.wheel.enter_inline_phase(r.now).unwrap();assert!(r.issue(&a).unwrap());
    assert_eq!(r.pending_issue.get(&0).map(BTreeSet::len),Some(1));
    assert_eq!(r.inflight.get(&0).map(BTreeSet::len).unwrap_or(0),0);
    assert_eq!(r.sequences.iter().filter(|s|s.issue.is_some()).count(),0);
    assert!(!r.issue(&a).unwrap());assert_eq!(r.sequences[1].reservation,None);
    r.start(&a,0).unwrap();assert_eq!(r.activities.len(),1);assert_eq!(r.activities[0].end,60000);
    assert_eq!(r.counts.read,0);assert_eq!(r.counts.sram_write,0);
}
#[test]
fn proposed_zero_alignment_has_no_new_issue_rate_cap() {
    let (_,mut a)=fixture("D07");a.hardware.credit_limit=64;
    let r=Runtime::new_version(&a,ObservationVersion::V3).unwrap().run(&a).unwrap();
    assert_eq!(r.sequences.len(),33);assert!(r.sequences.iter().all(|s|s.reservation==Some(0)&&s.issue==Some(0)));
    assert_eq!(r.activities.iter().filter(|x|x.phase.name=="dma_issue"&&x.alignment&&x.start==0&&x.end==0).count(),33);
}
