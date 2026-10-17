//! PRIVATE SYNTHETIC unit anchors; no public authority or successful public invocation.
use crate::{admission::Trust, component, wire};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
fn fixture(id: &str) -> (Value, Trust) {
    let all: Value =
        serde_json::from_str(include_str!("../testdata/synthetic-component-jobs.json")).unwrap();
    let v = if id == "SYNTHETIC-O2-transient" {
        serde_json::from_str(include_str!(
            "../testdata/synthetic-component-transient-job.json"
        ))
        .unwrap()
    } else {
        all[id].clone()
    };
    assert!(!v.is_null(), "missing synthetic case {id}");
    let trust = Trust {
        registry: v["registry"]["registry_hash"].as_str().unwrap().into(),
        profiles: BTreeMap::from([(
            v["profile"]["profile_hash"].as_str().unwrap().into(),
            BTreeSet::from([v["admission"]["case_id"].as_str().unwrap().into()]),
        )]),
        engine: v["engine"].clone(),
    };
    (v, trust)
}
fn run(id: &str) -> Value {
    let (v, t) = fixture(id);
    component::execute(&wire::canonical(&v).unwrap(), &t).unwrap()
}
#[test]
fn synthetic_compute_literals() {
    let r = run("C02");
    assert_eq!(r["duration_ps"], 547000);
    assert_eq!(r["counts"]["matrix_ops"].as_f64(), Some(210.0));
    assert_eq!(r["work_counts"]["issued_matrix_ops"], 393216);
    assert_eq!(r["ext_counts"]["sram_read_bytes"].as_f64(), Some(100.0));
    assert_eq!(r["ext_counts"]["sram_write_bytes"].as_f64(), Some(42.0));
}
#[test]
fn synthetic_dma_literals() {
    for (id, end) in [
        ("D01", 60000),
        ("D02", 60000),
        ("D03", 69000),
        ("D04", 84000),
        ("D05-one", 120000),
        ("D06-two", 120000),
        ("D07", 132000),
        ("D08", 61000),
    ] {
        let r = run(id);
        assert_eq!(r["duration_ps"], end, "{id}");
    }
}
#[test]
fn synthetic_no_external_trust_from_self_hash() {
    let (v, mut t) = fixture("C02");
    t.profiles.clear();
    assert_eq!(
        component::execute(&wire::canonical(&v).unwrap(), &t)
            .unwrap_err()
            .code,
        "TestProfileMismatch"
    );
}
#[test]
fn synthetic_replay_is_complete_bytes() {
    for id in ["C02", "D01", "D08", "D14"] {
        let a = wire::canonical(&run(id)).unwrap();
        assert_eq!(a, wire::canonical(&run(id)).unwrap());
        assert_eq!(a, wire::canonical(&run(id)).unwrap());
    }
}

#[test]
fn synthetic_exact_channel_carry_and_refresh() {
    let r = run("D04");
    let rows = r["observations"]["resource_intervals"]["records"]
        .as_array()
        .unwrap();
    let channels: Vec<_> = rows
        .iter()
        .filter(|a| a["activity"] == "channel_service")
        .collect();
    assert_eq!(channels.len(), 12);
    assert_eq!(channels[0]["end_ps"], 54250);
    assert_eq!(channels[11]["end_ps"], 78999);
    assert_eq!(channels[11]["service_end_ps_ratio"]["numerator"], 5608928);
    assert_eq!(channels[11]["service_end_ps_ratio"]["denominator"], 71);
}
#[test]
fn synthetic_credit_and_shared_port_literals() {
    for (id, issues, ends) in [
        ("D05-one", vec![0, 60000], vec![60000, 120000]),
        ("D05-two", vec![0, 0], vec![60000, 62000]),
        ("D06-full", vec![0, 0, 0], vec![60000, 62000, 64000]),
        ("D08", vec![0, 0], vec![60000, 61000]),
    ] {
        let r = run(id);
        let reqs = r["observations"]["dma"]["records"].as_array().unwrap();
        assert_eq!(
            reqs.iter()
                .map(|x| x["issue_ps"].as_u64().unwrap())
                .collect::<Vec<_>>(),
            issues,
            "{id}"
        );
        assert_eq!(
            reqs.iter()
                .map(|x| x["complete_ps"].as_u64().unwrap())
                .collect::<Vec<_>>(),
            ends,
            "{id}"
        );
        assert!(
            reqs.iter()
                .all(|x| x["complete_ps"] == x["credit_release_ps"])
        );
    }
}
#[test]
fn synthetic_zero_hop_and_unequal_clocks() {
    for (id, end) in [
        ("D14", 61000),
        ("D10-read", 63750),
        ("D13-hop", 4000),
        ("SYNTHETIC-D13-barrier-owner", 94000),
    ] {
        let r = run(id);
        assert_eq!(r["duration_ps"], end, "{id}");
    }
    let r = run("D14");
    let acts = r["observations"]["activities"]["records"]
        .as_array()
        .unwrap();
    assert!(acts.iter().any(|a| a["subphase"] == "unicast_noc"
        && a["start_ps"] == a["end_ps"]
        && a["occupies_resource"] == false));
}
#[test]
fn synthetic_rational_overflow_is_checked() {
    use crate::component::Ratio;
    assert!(Ratio::new(1, 0).is_err());
    assert!(
        Ratio::new(u128::MAX, 1)
            .unwrap()
            .plus(Ratio::integer(1))
            .is_err()
    );
    assert!(Ratio::new(u128::MAX, 1).unwrap().ceil().is_err());
    assert_eq!(Ratio::new(4, 6).unwrap(), Ratio::new(2, 3).unwrap());
}
#[test]
#[ignore = "explicit PRIVATE SYNTHETIC output export; never public respond or host authority"]
fn export_private_synthetic_results() {
    let root = std::path::PathBuf::from(
        std::env::var("COMPONENT_PRIVATE_OUTPUT").expect("explicit private output"),
    );
    std::fs::create_dir_all(&root).unwrap();
    let all: Value =
        serde_json::from_str(include_str!("../testdata/synthetic-component-jobs.json")).unwrap();
    let mut names = vec![];
    for id in all.as_object().unwrap().keys() {
        if id == "D13-barrier" {
            let (v, t) = fixture(id);
            assert_eq!(
                component::execute(&wire::canonical(&v).unwrap(), &t)
                    .unwrap_err()
                    .code,
                "InvalidResource"
            );
            continue;
        }
        let result = run(id);
        std::fs::write(
            root.join(format!("{id}.json")),
            wire::canonical(&result).unwrap(),
        )
        .unwrap();
        names.push(id.clone());
    }
    let id = "SYNTHETIC-O2-transient";
    std::fs::write(
        root.join(format!("{id}.json")),
        wire::canonical(&run(id)).unwrap(),
    )
    .unwrap();
    names.push(id.into());
    assert_eq!(names.len(), 79);
    std::fs::write(root.join("index.json"), serde_json::to_vec(&names).unwrap()).unwrap();
}

#[test]
fn synthetic_phase_inventory_and_completed_traffic() {
    let r = run("C02");
    let o = &r["observations"];
    assert_eq!(o["activities"]["records"].as_array().unwrap().len(), 8);
    assert_eq!(o["events"]["records"].as_array().unwrap().len(), 16);
    assert_eq!(o["clocks"]["records"].as_array().unwrap().len(), 8);
    assert_eq!(
        o["resource_intervals"]["records"].as_array().unwrap().len(),
        4
    );
    let r = run("D01");
    let o = &r["observations"];
    assert_eq!(o["activities"]["records"].as_array().unwrap().len(), 9);
    assert_eq!(o["events"]["records"].as_array().unwrap().len(), 18);
    assert_eq!(
        o["resource_intervals"]["records"].as_array().unwrap().len(),
        4
    );
    assert_eq!(r["attribution_ps"]["noc"], 8750);
    assert_eq!(r["attribution_ps"]["memory"], 51250);
    for (id, payload, txn) in [("D11", 513, 768), ("D12", 2, 512)] {
        let r = run(id);
        assert_eq!(r["traffic_counts"]["read_payload_bytes"], payload);
        assert_eq!(r["traffic_counts"]["read_transaction_bytes"], txn);
        assert_eq!(
            r["observations"]["dma"]["records"]
                .as_array()
                .unwrap()
                .len() as u64,
            txn / 256
        );
    }
}
#[test]
fn synthetic_transient_all_terminal_readers() {
    let r = run("SYNTHETIC-O2-transient");
    assert_eq!(r["duration_ps"], 2735000);
    assert_eq!(r["work_counts"]["completed_mac_count"], 525);
    let a = r["observations"]["allocations"]["records"]
        .as_array()
        .unwrap()
        .iter()
        .find(|a| a["buffer_id"] == "bacc")
        .unwrap();
    assert_eq!(a["allocate_ps"], 547000);
    assert_eq!(a["free_ps"], 2188000);
    assert_eq!(a["last_consumer_ids"], serde_json::json!(["c", "d"]));
    let jobs = r["observations"]["jobs"]["records"].as_array().unwrap();
    assert_eq!(
        jobs.iter().find(|j| j["job_id"] == "d").unwrap()["ready_ps"],
        1094000
    );
    assert_eq!(
        jobs.iter().find(|j| j["job_id"] == "d").unwrap()["start_ps"],
        1641000
    );
}

#[test]
fn synthetic_installed_issue_core_gap_is_explicit_refusal() {
    let v: Value =
        serde_json::from_str(include_str!("../testdata/synthetic-issue-core-gap.json")).unwrap();
    let t = Trust {
        registry: v["registry"]["registry_hash"].as_str().unwrap().into(),
        profiles: BTreeMap::from([(
            v["profile"]["profile_hash"].as_str().unwrap().into(),
            BTreeSet::from([v["admission"]["case_id"].as_str().unwrap().into()]),
        )]),
        engine: v["engine"].clone(),
    };
    crate::component_admission::validate(&wire::canonical(&v).unwrap(), &t).unwrap();
    assert_eq!(
        component::execute(&wire::canonical(&v).unwrap(), &t)
            .unwrap_err()
            .code,
        "IncompleteObservations"
    );
}
