//! Stage 2 regressions authored before the proposed implementation corrections.
use crate::*;
fn job(id: u32, owner: u32, ps: u64, deps: &[u32]) -> Job {
    Job {
        id,
        owner,
        duration: Delay::Picoseconds(ps),
        dependencies: deps.to_vec(),
    }
}
#[test]
fn lowest_owner_zero_closure_has_literal_110ps_path() {
    // z0 enables a(10ps) before z1 enables b(1ps), both on owner2. tail waits a.
    // Low-owner-first: a[0,10), b[10,11), tail[10,110). Reversed: b[0,1),
    // a[1,11), tail[11,111). A repeated-run equality check cannot distinguish these.
    let r = Simulation::new(
        vec![1_000_000_000],
        4,
        vec![
            job(0, 0, 0, &[]),
            job(1, 1, 0, &[]),
            job(2, 2, 10, &[0]),
            job(3, 2, 1, &[1]),
            job(4, 3, 100, &[2]),
        ],
    )
    .unwrap()
    .run()
    .unwrap();
    assert_eq!(r.duration_ps, 110);
    assert_eq!(
        (r.jobs[2].start_ps, r.jobs[3].start_ps, r.jobs[4].end_ps),
        (0, 10, 110)
    );
}
#[test]
fn same_timestamp_regression_refuses_but_forward_insertions_work() {
    let mut w = Wheel::new(1_000_000_000).unwrap();
    w.schedule(100, 2, 5, Kind::TaskReady, 0).unwrap();
    w.pop().unwrap();
    assert_eq!(
        w.schedule(100, 0, 0, Kind::TaskReady, 0),
        Err(Error::PastEvent)
    );
    assert_eq!(
        w.schedule(100, 2, 4, Kind::TaskReady, 0),
        Err(Error::PastEvent)
    );
    // Same target with later sequence, higher target, next phase with lower target,
    // and future timestamp with lower phase all preserve the queued total order.
    for (t, p, o) in [(100, 2, 5), (100, 2, 6), (100, 3, 0), (101, 0, 0)] {
        w.schedule(t, p, o, Kind::TaskReady, 0).unwrap();
    }
    let mut keys = Vec::new();
    while let Some(e) = w.pop() {
        keys.push(e.key());
    }
    assert!(keys.windows(2).all(|x| x[0] < x[1]));
    assert_eq!(keys.len(), 4);
}
#[test]
fn unsupported_wheel_phase_refuses() {
    let mut w = Wheel::new(1).unwrap();
    assert_eq!(
        w.schedule(0, 4, 0, Kind::TaskReady, 0),
        Err(Error::InvalidEvent)
    );
    assert_eq!(
        w.schedule(0, 255, 0, Kind::TaskReady, 0),
        Err(Error::InvalidEvent)
    );
}
#[test]
fn private_predecessor_list_is_explicitly_noncausal() {
    // Reviewer's idle-owner example: owner0 idle from100 to1000. This field is an
    // unconditional, sorted unique dependency + previous-resource-job list, NOT blockers.
    let r = Simulation::new(
        vec![1],
        2,
        vec![
            job(1, 0, 100, &[]),
            job(2, 1, 1000, &[]),
            job(3, 0, 100, &[2]),
        ],
    )
    .unwrap()
    .run()
    .unwrap();
    let json: serde_json::Value = serde_json::from_slice(&r.canonical_bytes().unwrap()).unwrap();
    assert_eq!(
        json["jobs"][2]["dependency_resource_predecessors"],
        serde_json::json!([1, 2])
    );
    assert!(json["jobs"][2].get("blocking_predecessors").is_none());
    assert_eq!((r.jobs[2].ready_ps, r.jobs[2].start_ps), (1000, 1000));
    let r = Simulation::new(vec![1], 1, vec![job(1, 0, 10, &[]), job(2, 0, 20, &[1])])
        .unwrap()
        .run()
        .unwrap();
    let json: serde_json::Value = serde_json::from_slice(&r.canonical_bytes().unwrap()).unwrap();
    assert_eq!(
        json["jobs"][0]["dependency_resource_predecessors"],
        serde_json::json!([])
    );
    assert_eq!(
        json["jobs"][1]["dependency_resource_predecessors"],
        serde_json::json!([1])
    ); // deduplicated
}

#[test]
fn actual_dispatch_targets_and_inline_kinds_are_observed() {
    let r = Simulation::new(
        vec![1_000_000_000],
        2,
        vec![
            job(0, 0, 3000, &[]),
            job(1, 1, 1000, &[]),
            job(2, 0, 0, &[1]),
            job(3, 1, 2000, &[2]),
        ],
    )
    .unwrap()
    .run()
    .unwrap();
    let bytes = r.canonical_bytes().unwrap();
    let value: serde_json::Value = serde_json::from_slice(&bytes).unwrap();
    for row in value["records"].as_array().unwrap() {
        assert_eq!(row["owner"], row["event_target"]);
    }
    assert_eq!(r.duration_ps, 5000);
    assert!(
        r.records
            .iter()
            .any(|e| e.event_kind == Kind::DependencyReady as u16 && !e.inline)
    );
    assert!(
        r.records
            .iter()
            .any(|e| e.event_kind == Kind::DependencyReady as u16 && e.inline)
    );
    assert!(
        r.records
            .iter()
            .any(|e| e.event_kind == Kind::OwnerGrant as u16 && e.inline)
    );
    assert!(r.records.iter().any(|e| e.job_id == 2
        && e.action == Action::Complete
        && e.inline
        && e.phase == 2
        && e.event_kind == Kind::ComputeDone as u16));
}
