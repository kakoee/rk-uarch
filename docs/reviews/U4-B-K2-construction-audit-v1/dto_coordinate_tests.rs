//! B-owned admission-only test module in a disposable copy. Never calls Simulation.
#[test]
fn b_independent_coordinate_vectors() {
    let cases: serde_json::Value = serde_json::from_str(include_str!("../testdata/b-dto-coordinate-vectors.json")).unwrap();
    let mut mismatches = Vec::new();
    for c in cases.as_array().unwrap() {
        let t=&c["trust"];
        let trust=crate::admission::Trust {registry:t["registry"].as_str().unwrap().into(),profiles:std::collections::BTreeMap::from([(t["profile"].as_str().unwrap().into(),std::collections::BTreeSet::from([t["case"].as_str().unwrap().into()]))]),engine:t["engine"].clone()};
        let actual = crate::admission::validate(c["input"].as_str().unwrap(), &trust);
        let good = match actual {
            Ok(v) => c["expected"] == "accept" && crate::wire::canonical(&v.raw).unwrap() == c["normalized"].as_str().unwrap_or(""),
            Err(e) => { if c["expected"] == "accept" { eprintln!("wrong refusal {}: {:?}", c["id"], e); } c["expected"] == "refuse" },
        };
        if !good { mismatches.push(c["id"].clone()); }
    }
    assert!(mismatches.is_empty(), "actual public DTO discrepancies: {mismatches:?}");
}
