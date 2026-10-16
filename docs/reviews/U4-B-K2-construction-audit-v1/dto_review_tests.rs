//! B-owned admission-only test module in a disposable copy. Never calls Simulation.
#[test]
fn b_independent_full_carrier_vectors() {
    let cases: serde_json::Value = serde_json::from_str(include_str!("../testdata/b-dto-vectors.json")).unwrap();
    let base: serde_json::Value = serde_json::from_str(include_str!("../testdata/synthetic-kernel-job.json")).unwrap();
    let trust = crate::admission::Trust {
        registry: base["registry"]["registry_hash"].as_str().unwrap().into(),
        profiles: std::collections::BTreeMap::from([(
            base["profile"]["profile_hash"].as_str().unwrap().into(),
            std::collections::BTreeSet::from([base["admission"]["case_id"].as_str().unwrap().into()]),
        )]),
        engine: base["engine"].clone(),
    };
    let mut mismatches = Vec::new();
    for c in cases.as_array().unwrap() {
        let actual = crate::admission::validate(c["input"].as_str().unwrap(), &trust);
        let good = match actual {
            Ok(v) => c["expected"] == "accept" && crate::wire::canonical(&v.raw).unwrap() == c["normalized"].as_str().unwrap_or(""),
            Err(e) => { if c["expected"] == "accept" { eprintln!("wrong refusal {}: {:?}", c["id"], e); } c["expected"] == "refuse" },
        };
        if !good { mismatches.push(c["id"].clone()); }
    }
    assert!(mismatches.is_empty(), "actual public DTO discrepancies: {mismatches:?}");
}
