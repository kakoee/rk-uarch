//! PRIVATE UNAPPLIED /3 tests. Typed-state probes are not claimed as mapped admission.
use super::*;
use crate::component_admission::Task;
use serde_json::json;

fn fixture(id: &str) -> (Value, Admitted) {
    let all: Value =
        serde_json::from_str(include_str!("../testdata/synthetic-component-jobs.json")).unwrap();
    let v = all[id].clone();
    let a = component_admission::validate(&crate::wire::canonical(&v).unwrap()).unwrap();
    (v, a)
}
fn model_two(v: &mut Value) {
    v["engine"]["model"]["version"] = json!("2");
    v.as_object_mut().unwrap().remove("job_hash");
    v["job_hash"] = json!(crate::hardware::digest(v).unwrap());
}
// Direct typed-state synthesis after real baseline admission. No result-carrier claim.
fn boundary(write: bool, ready: u64, cap: u64, independent: bool) -> Admitted {
    let (_, mut a) = fixture(if write { "D02" } else { "D01" });
    a.hardware.as_mut().unwrap().freq[1] = 1_000_000_000_000;
    a.hardware.as_mut().unwrap().hop_cycles = 2000;
    a.hardware.as_mut().unwrap().barrier_cycles = ready;
    a.hardware.as_mut().unwrap().credit_limit = cap;
    let mut second = a.graph.jobs[0].clone();
    second.id = "second".into();
    if let TaskKind::Dma {
        engine,
        source,
        destination,
        fragments,
        ..
    } = &mut second.kind
    {
        if independent {
            *engine = 1;
            second.owner += 1;
        }
        *source = format!("second-{source}");
        *destination = format!("second-{destination}");
        fragments[0].id = "second.0".into();
    }
    let extra: Vec<_> = a
        .graph
        .buffers
        .iter()
        .cloned()
        .map(|mut b| {
            b.id = format!("second-{}", b.id);
            b.producer = b.producer.map(|_| 1);
            b.consumers = b.consumers.iter().map(|_| 1).collect();
            b
        })
        .collect();
    a.graph.buffers.extend(extra);
    a.graph.jobs.push(second);
    a.graph.jobs.push(Task {
        id: "barrier".into(),
        op_id: None,
        owner: 52,
        kind: TaskKind::Barrier,
        raw: json!({}),
    });
    a.graph.dependencies = vec![(2, 1)];
    a
}
fn issue_alignment(r: &Runtime, sequence: usize) -> &Activity {
    r.activities
        .iter()
        .find(|x| x.sequence == sequence && x.phase.name == "dma_issue" && x.alignment)
        .expect("explicit issue alignment")
}
#[test]
fn proposed_raw_gap_has_exact_issue_alignment_and_queues() {
    let mut v: Value =
        serde_json::from_str(include_str!("../testdata/synthetic-issue-core-gap.json")).unwrap();
    model_two(&mut v);
    let r = execute_with_observations(&crate::wire::canonical(&v).unwrap(), ObservationVersion::V3)
        .unwrap();
    assert_eq!(r["observations"]["format"], "uarch-native-observations/3");
    let rows = r["observations"]["activities"]["records"]
        .as_array()
        .unwrap();
    let align = rows
        .iter()
        .find(|x| x["subphase"] == "dma_issue" && x["kind"] == "alignment")
        .unwrap();
    assert_eq!(
        (
            align["ready_ps"].as_u64(),
            align["start_ps"].as_u64(),
            align["end_ps"].as_u64()
        ),
        (Some(26667), Some(26667), Some(27000))
    );
    assert_eq!(align["occupies_resource"], false);
    let service = rows
        .iter()
        .find(|x| x["subphase"] == "dma_issue" && x["kind"] == "service")
        .unwrap();
    assert_eq!(service["start_ps"], 27000);
    assert_eq!(service["end_ps"], 27000);
    let dma = r["observations"]["dma"]["records"]
        .as_array()
        .unwrap()
        .iter()
        .find(|x| x["direction"] == "read")
        .unwrap();
    assert_eq!(dma["reservation_ps"], 26667);
    assert_eq!(dma["issue_ps"], 27000);
    assert_eq!(dma["credit_acquire_ps"], 27000);
    let q = r["observations"]["queue_membership"]["records"]
        .as_array()
        .unwrap();
    let pending = q.iter().find(|x| x["queue_id"] == "dma_pending:0").unwrap();
    assert_eq!(pending["population"], "pending");
    assert_eq!(pending["enter_ps"], 26667);
    assert_eq!(pending["leave_ps"], 27000);
    assert!(pending["clock_domain"].is_null());
    assert!(pending["activity_id"].is_null());
}
#[test]
fn proposed_model_version_is_explicit_and_legacy_is_unchanged() {
    let (v, _) = fixture("D01");
    let raw = crate::wire::canonical(&v).unwrap();
    let old = execute(&raw).unwrap();
    assert_eq!(old["duration_ps"], 60000);
    assert_eq!(old["observations"]["format"], "uarch-native-observations/2");
    assert!(
        old["observations"]["dma"]["records"][0]
            .get("reservation_ps")
            .is_none()
    );
    let mut new_input = v.clone();
    model_two(&mut new_input);
    assert_eq!(
        execute(&crate::wire::canonical(&new_input).unwrap())
            .unwrap_err()
            .code,
        "InvalidCarrier"
    );
    assert_eq!(
        execute_with_observations(&raw, ObservationVersion::V3)
            .unwrap_err()
            .code,
        "InvalidCarrier"
    );
}
#[test]
fn proposed_read_write_credit_cause_boundary_is_reservation_time() {
    for write in [false, true] {
        for ready in [59999, 60000, 60001] {
            let a = boundary(write, ready, 1, false);
            let r = Runtime::new_version(&a, ObservationVersion::V3)
                .unwrap()
                .run(&a)
                .unwrap();
            assert_eq!(r.sequences[0].end, Some(60000));
            assert_eq!(r.sequences[1].reservation, Some(ready.max(60000)));
            assert_eq!(
                r.sequences[1].issue,
                Some(if ready == 60001 { 61000 } else { 60000 })
            );
            let align = issue_alignment(&r, 1);
            let relations: BTreeSet<_> = align.causes.iter().map(|x| x.1).collect();
            assert_eq!(
                relations,
                BTreeSet::from([if ready == 59999 {
                    "credit"
                } else {
                    "dependency"
                }])
            );
            assert_eq!(r.jobs[1].start, r.sequences[1].reservation);
            assert_eq!(r.events[align.dispatch as usize].phase, 2);
            for (cause, _) in &align.causes {
                assert!(r.activities[*cause].completion < align.dispatch);
                let prior = &r.activities[*cause];
                assert_eq!(
                    r.events[prior.completion as usize].phase,
                    if prior.end > prior.start { 0 } else { 2 }
                );
            }
            assert!(
                r.activities
                    .iter()
                    .filter(|x| x.sequence == 1 && x.phase.name != "dma_issue")
                    .all(|x| x.start >= r.sequences[1].issue.unwrap())
            );
            for (i, b) in a
                .graph
                .buffers
                .iter()
                .enumerate()
                .filter(|(_, b)| b.producer == Some(1))
            {
                assert!(!b.persistent);
                assert_eq!(r.allocations[i].start, r.jobs[1].start);
            }
        }
    }
}
#[test]
fn proposed_cap_two_and_independent_engines_reserve_before_issue() {
    for (cap, independent) in [(2, false), (1, true)] {
        for write in [false, true] {
            let a = boundary(write, 59999, cap, independent);
            let r = Runtime::new_version(&a, ObservationVersion::V3)
                .unwrap()
                .run(&a)
                .unwrap();
            assert_eq!(r.sequences[1].reservation, Some(59999));
            assert_eq!(r.sequences[1].issue, Some(60000));
            assert_eq!(
                issue_alignment(&r, 1)
                    .causes
                    .iter()
                    .map(|x| x.1)
                    .collect::<Vec<_>>(),
                vec!["dependency"]
            );
        }
    }
}
#[test]
fn proposed_cap_one_pending_reservation_prevents_double_issue() {
    let mut a = boundary(false, 59999, 1, false);
    a.graph.dependencies = vec![(2, 0), (2, 1)];
    let mut r = Runtime::new_version(&a, ObservationVersion::V3).unwrap();
    // Explicit private scheduler state at dependency completion; inspect before any payload step.
    r.now = 59999;
    r.jobs[2].ready = Some(0);
    r.jobs[2].end = Some(59999);
    r.ready_jobs(&a);
    r.wheel.enter_inline_phase(r.now).unwrap();
    assert!(r.issue(&a).unwrap());
    assert_eq!(r.pending_issue.get(&0).map(BTreeSet::len), Some(1));
    assert_eq!(r.inflight.get(&0).map(BTreeSet::len).unwrap_or(0), 0);
    assert_eq!(r.sequences.iter().filter(|s| s.issue.is_some()).count(), 0);
    assert!(!r.issue(&a).unwrap());
    assert_eq!(r.sequences[1].reservation, None);
    r.start(&a, 0).unwrap();
    assert_eq!(r.activities.len(), 1);
    assert_eq!(r.activities[0].end, 60000);
    assert_eq!(r.counts.read, 0);
    assert_eq!(r.counts.sram_write, 0);
}
#[test]
fn proposed_zero_alignment_has_no_new_issue_rate_cap() {
    let (_, mut a) = fixture("D07");
    a.hardware.as_mut().unwrap().credit_limit = 64;
    let r = Runtime::new_version(&a, ObservationVersion::V3)
        .unwrap()
        .run(&a)
        .unwrap();
    assert_eq!(r.sequences.len(), 33);
    assert!(
        r.sequences
            .iter()
            .all(|s| s.reservation == Some(0) && s.issue == Some(0))
    );
    assert_eq!(
        r.activities
            .iter()
            .filter(|x| x.phase.name == "dma_issue" && x.alignment && x.start == 0 && x.end == 0)
            .count(),
        33
    );
}

#[test]
fn proposed_two_simultaneous_pending_credits_are_distinct_from_inflight() {
    let mut a = boundary(false, 59999, 2, false);
    a.graph.dependencies = vec![(2, 0), (2, 1)];
    let r = Runtime::new_version(&a, ObservationVersion::V3)
        .unwrap()
        .run(&a)
        .unwrap();
    assert_eq!(r.sequences[0].reservation, Some(59999));
    assert_eq!(r.sequences[1].reservation, Some(59999));
    assert_eq!(r.sequences[0].issue, Some(60000));
    assert_eq!(r.sequences[1].issue, Some(60000));
    assert_eq!(r.jobs[0].start, Some(59999));
    assert_eq!(r.jobs[1].start, Some(59999));
    assert_eq!(r.counts.read, 512);
    assert_eq!(r.counts.read_txn, 512);
    assert!(r.pending_issue.values().all(BTreeSet::is_empty));
    assert!(r.inflight.values().all(BTreeSet::is_empty));
}

#[test]
fn proposed_v2_full_bytes_remain_frozen_for_compute_read_write() {
    {
        let (v, _) = fixture("C02");
        let r = execute(&crate::wire::canonical(&v).unwrap()).unwrap();
        assert_eq!(
            crate::hardware::digest(&r).unwrap(),
            "sha256:aa477f0f69c80aea072ae52b7b6c306597177ed5c95325b6ae0301564cfff4ce"
        );
    }
    {
        let (v, _) = fixture("D01");
        let r = execute(&crate::wire::canonical(&v).unwrap()).unwrap();
        assert_eq!(
            crate::hardware::digest(&r).unwrap(),
            "sha256:cdbae721a6966af5a33116fbd229aa776c13d02e768767fbfa56737df53de863"
        );
    }
    {
        let (v, _) = fixture("D02");
        let r = execute(&crate::wire::canonical(&v).unwrap()).unwrap();
        assert_eq!(
            crate::hardware::digest(&r).unwrap(),
            "sha256:ab579d0eca3929d4ebb4cccd87cba7eb2995c23a717c4b9aad7041e4f7d9ae4e"
        );
    }
}

#[test]
fn proposed_added_endpoints_preserve_event_capacity_bound() {
    // PRIVATE typed-state capacity discriminator, not a mapped/admitted duplicate-ID job.
    let (_, mut a) = fixture("D02");
    if let TaskKind::Dma { fragments, .. } = &mut a.graph.jobs[0].kind {
        *fragments = vec![fragments[0].clone(); 35715];
    }
    assert_eq!(
        Runtime::new_version(&a, ObservationVersion::V3)
            .err()
            .unwrap()
            .code,
        "CapacityExceeded"
    );
    assert!(Runtime::new_version(&a, ObservationVersion::V2).is_ok());
}

fn ordering_probe(raw: &str, first: &str, second: &str) {
    let result = execute_with_observations(raw, ObservationVersion::V3).unwrap();
    let opportunities = result["observations"]["reservation_opportunities"]["records"]
        .as_array()
        .expect("actual reservation opportunities required");
    assert_eq!(opportunities.len(), 5);
    assert_eq!(
        opportunities[0],
        json!({"opportunity_ordinal":0,"t_ps":0,"event_cursor":0,"granted_request_ids":[first]})
    );
    assert_eq!(
        opportunities[1],
        json!({"opportunity_ordinal":1,"t_ps":0,"event_cursor":2,"granted_request_ids":[]})
    );
    assert_eq!(
        opportunities
            .iter()
            .map(|x| x["t_ps"].as_u64().unwrap())
            .collect::<Vec<_>>(),
        vec![0, 0, 26667, 60000, 120000]
    );
    assert_eq!(opportunities[2]["granted_request_ids"], json!([]));
    assert_eq!(opportunities[3]["granted_request_ids"], json!([second]));
    assert_eq!(opportunities[4]["granted_request_ids"], json!([]));
    for (i, row) in opportunities.iter().enumerate() {
        assert_eq!(row["opportunity_ordinal"], json!(i));
    }
    let dma = result["observations"]["dma"]["records"].as_array().unwrap();
    let first_dma = dma.iter().find(|x| x["request_id"] == first).unwrap();
    let second_dma = dma.iter().find(|x| x["request_id"] == second).unwrap();
    assert_eq!(
        (
            first_dma["reservation_ps"].as_u64(),
            first_dma["issue_ps"].as_u64(),
            first_dma["complete_ps"].as_u64()
        ),
        (Some(0), Some(0), Some(60000))
    );
    assert_eq!(
        (
            second_dma["reservation_ps"].as_u64(),
            second_dma["issue_ps"].as_u64(),
            second_dma["complete_ps"].as_u64()
        ),
        (Some(60000), Some(60000), Some(120000))
    );
    let align = result["observations"]["activities"]["records"]
        .as_array()
        .unwrap()
        .iter()
        .find(|x| {
            x["request_id"] == first && x["subphase"] == "dma_issue" && x["kind"] == "alignment"
        })
        .unwrap();
    assert!(
        align["dispatch_ordinal"].as_u64().unwrap() > 0,
        "alignment dispatch is later than actual reservation"
    );
}
#[test]
fn proposed_order_inline_dependency_is_later_eligibility() {
    ordering_probe(
        include_str!("../testdata/synthetic-issue-order-r00.json"),
        "r01.00",
        "r00.00",
    );
}
#[test]
fn proposed_order_paired_inline_dependency_preserves_initial_grant() {
    ordering_probe(
        include_str!("../testdata/synthetic-issue-order-r01.json"),
        "r00.00",
        "r01.00",
    );
}

#[test]
fn proposed_order_terminal_phase_zero_batch_and_inline_epochs() {
    // Private typed state: isolate two terminal transitions, not mapped admission.
    for cycles in [0, 32] {
        let (_, mut a) = fixture("D01");
        a.hardware.as_mut().unwrap().barrier_cycles = cycles;
        a.graph.jobs = (0..2)
            .map(|i| Task {
                id: format!("barrier-{i}"),
                op_id: None,
                owner: 52 + i,
                kind: TaskKind::Barrier,
                raw: json!({}),
            })
            .collect();
        a.graph.dependencies.clear();
        a.graph.buffers.clear();
        let state = Runtime::new_version(&a, ObservationVersion::V3)
            .unwrap()
            .run(&a)
            .unwrap();
        let cursors = state
            .reservation_opportunities
            .iter()
            .map(|x| x.event_cursor)
            .collect::<Vec<_>>();
        assert_eq!(
            cursors,
            if cycles == 0 {
                vec![0, 4, 8]
            } else {
                vec![0, 8]
            }
        );
        assert!(
            state
                .reservation_opportunities
                .iter()
                .all(|x| x.granted.is_empty())
        );
        assert_eq!(state.events.len(), 8);
        assert_eq!(
            state.events.iter().filter(|x| x.phase == 0).count(),
            if cycles == 0 { 0 } else { 2 }
        );
    }
}

fn stage2_result(raw: &str) -> Value {
    execute_with_observations(raw, ObservationVersion::V3).unwrap()
}
fn stage2_mixed_causes(raw: &str, release: u64) {
    let r = stage2_result(raw);
    let rows = r["observations"]["activities"]["records"]
        .as_array()
        .unwrap();
    let opportunities = r["observations"]["reservation_opportunities"]["records"]
        .as_array()
        .unwrap();
    for (request, cursor, expected) in [
        ("r02.00", 52, vec![("r00", "read_port", 50)]),
        (
            "r03.00",
            56,
            vec![("r00", "read_port", 50), ("r01", "ack", 55)],
        ),
    ] {
        let opportunity = opportunities
            .iter()
            .find(|o| {
                o["granted_request_ids"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .any(|x| x == request)
            })
            .unwrap();
        assert_eq!(opportunity["event_cursor"], cursor);
        assert_eq!(opportunity["t_ps"], release);
        let alignment = rows
            .iter()
            .find(|a| {
                a["request_id"] == request
                    && a["subphase"] == "dma_issue"
                    && a["kind"] == "alignment"
            })
            .unwrap();
        let mut causes = alignment["predecessors"]
            .as_array()
            .unwrap()
            .iter()
            .filter(|p| p["relation"] == "credit")
            .map(|p| {
                let a = rows
                    .iter()
                    .find(|a| a["activity_id"] == p["activity_id"])
                    .unwrap();
                assert_eq!(a["kind"], "service");
                assert_eq!(a["end_ps"], release);
                assert!(a["completion_ordinal"].as_u64().unwrap() < cursor);
                (
                    a["job_id"].as_str().unwrap(),
                    a["subphase"].as_str().unwrap(),
                    a["completion_ordinal"].as_u64().unwrap(),
                )
            })
            .collect::<Vec<_>>();
        causes.sort();
        assert_eq!(causes, expected);
    }
}
#[test]
fn proposed_stage2_cc0_retains_all_observed_same_instant_releases() {
    stage2_mixed_causes(
        include_str!("../testdata/synthetic-stage2-cc0-v3.json"),
        60000,
    );
}
#[test]
fn proposed_stage2_gapped_cc_retains_all_observed_same_instant_releases() {
    stage2_mixed_causes(
        include_str!("../testdata/synthetic-stage2-cc-v3.json"),
        86000,
    );
}
#[test]
fn proposed_stage2_sr_waits_for_own_engine_inline_release() {
    let r = stage2_result(include_str!("../testdata/synthetic-stage2-sr-v3.json"));
    let opportunities = r["observations"]["reservation_opportunities"]["records"]
        .as_array()
        .unwrap();
    let early = opportunities
        .iter()
        .find(|o| o["event_cursor"] == 52)
        .unwrap();
    assert_eq!(early["t_ps"], 86000);
    assert_eq!(early["granted_request_ids"], json!([]));
    let grant = opportunities
        .iter()
        .find(|o| o["event_cursor"] == 54)
        .unwrap();
    assert_eq!(grant["t_ps"], 86000);
    assert_eq!(grant["granted_request_ids"], json!(["r02.00"]));
    let rows = r["observations"]["activities"]["records"]
        .as_array()
        .unwrap();
    let alignment = rows
        .iter()
        .find(|a| {
            a["request_id"] == "r02.00" && a["subphase"] == "dma_issue" && a["kind"] == "alignment"
        })
        .unwrap();
    let causes = alignment["predecessors"]
        .as_array()
        .unwrap()
        .iter()
        .filter(|p| p["relation"] == "credit")
        .collect::<Vec<_>>();
    assert_eq!(causes.len(), 1);
    let cause = rows
        .iter()
        .find(|a| a["activity_id"] == causes[0]["activity_id"])
        .unwrap();
    assert_eq!(
        (
            cause["job_id"].as_str(),
            cause["subphase"].as_str(),
            cause["completion_ordinal"].as_u64()
        ),
        (Some("r00"), Some("ack"), Some(53))
    );
    assert_eq!(cause["kind"], "service");
    assert_eq!(cause["end_ps"], 86000);
}
