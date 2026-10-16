//! Private Wheel/Arena and raw clock controls. No public event-injection carrier.
use crate::{Error, Kind, Wheel, next_edge};
use serde_json::{Value, json};
#[test]
fn b_100_frozen_wheel_schedules() {
    let cases: Value = serde_json::from_str(include_str!("../testdata/b-wheel-schedules.json")).unwrap();
    assert_eq!(cases.as_array().unwrap().len(),100);
    for c in cases.as_array().unwrap() {
        let mut w=Wheel::new(c["max_freq_hz"].as_u64().unwrap()).unwrap();
        for e in c["schedule"].as_array().unwrap() {
            let seq=w.schedule(e["t_ps"].as_u64().unwrap(),e["phase"].as_u64().unwrap() as u8,e["target"].as_u64().unwrap() as u32,Kind::TaskReady,e["payload"].as_u64().unwrap() as u32).unwrap();
            assert_eq!(seq,e["seq"].as_u64().unwrap());
        }
        for expected in c["expected_pop"].as_array().unwrap() {
            let e=w.pop().unwrap();
            assert_eq!(json!({"t_ps":e.t_ps,"phase":e.phase,"target":e.target,"seq":e.seq,"payload":e.payload}),*expected,"{}",c["case_id"]);
        }
        assert!(w.pop().is_none());
        let r=&c["reuse"];
        let seq=w.schedule(r["t_ps"].as_u64().unwrap(),r["phase"].as_u64().unwrap() as u8,r["target"].as_u64().unwrap() as u32,Kind::TaskReady,r["payload"].as_u64().unwrap() as u32).unwrap();
        assert_eq!(seq,r["seq"].as_u64().unwrap());let e=w.pop().unwrap();
        assert_eq!(json!({"t_ps":e.t_ps,"phase":e.phase,"target":e.target,"seq":e.seq,"payload":e.payload}),*r);
        assert!(w.pop().is_none());
    }
}
#[test]
fn b_raw_alignment_vs_owned_service_boundaries() {
    assert_eq!(next_edge(1_200_000_000,835,0),Ok(1667));
    assert_eq!(next_edge(1_000_000_000,u64::MAX,0),Err(Error::TimeOverflow));
    assert_eq!(next_edge(1_000_000_000_000,u64::MAX,0),Ok(u64::MAX));
    assert_eq!(next_edge(1_000_000_000_000,u64::MAX,1),Err(Error::TimeOverflow));
    // Owned zero-cycle completion at grant835/MAX was independently exercised by
    // b_133_private_literal_cases, including full release/grant intervals.
}
