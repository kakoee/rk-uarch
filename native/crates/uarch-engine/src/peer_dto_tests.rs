//! Published B vectors plus A frozen refusal classes. Admission only, no Simulation.
use crate::{
    admission::{Trust, validate},
    wire,
};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
#[test]
#[ignore = "explicit frozen private B DTO directory; admission only"]
fn published_peer_dto_cases() {
    let root = std::path::PathBuf::from(
        std::env::var("K2_PEER_DTO_DIR").expect("explicit frozen DTO directory"),
    );
    let expectations: Value =
        serde_json::from_slice(&std::fs::read(root.join("expectations.json")).unwrap()).unwrap();
    let base: Value =
        serde_json::from_str(include_str!("../testdata/synthetic-kernel-job.json")).unwrap();
    let mut count = 0;
    for file in ["b-dto.json", "b-keys.json", "b-coordinates.json"] {
        let cases: Value =
            serde_json::from_slice(&std::fs::read(root.join(file)).unwrap()).unwrap();
        assert!(!cases.as_array().unwrap().is_empty());
        for row in cases.as_array().unwrap() {
            let trust = if row.get("trust").is_some() {
                &row["trust"]
            } else {
                &serde_json::json!({"registry":base["registry"]["registry_hash"],"profile":base["profile"]["profile_hash"],"case":base["admission"]["case_id"],"engine":base["engine"]})
            };
            let t = Trust {
                registry: trust["registry"].as_str().unwrap().into(),
                profiles: BTreeMap::from([(
                    trust["profile"].as_str().unwrap().into(),
                    BTreeSet::from([trust["case"].as_str().unwrap().into()]),
                )]),
                engine: trust["engine"].clone(),
            };
            let key = format!("{}::{}", file, row["id"].as_str().unwrap());
            let expected = &expectations[&key];
            match validate(row["input"].as_str().unwrap(), &t) {
                Ok(v) => {
                    assert_eq!(expected["expected"], "accept", "{key}");
                    assert_eq!(
                        wire::canonical(&v.raw).unwrap(),
                        row["normalized"].as_str().unwrap(),
                        "{key}"
                    );
                }
                Err(e) => {
                    assert_eq!(expected["expected"], "refuse", "{key}: {e:?}");
                    assert_eq!(expected["code"], e.code, "{key}: {e:?}");
                }
            }
            count += 1;
        }
    }
    assert_eq!(count, 48);
    println!(
        "48 complete-carrier cases; exact canonical bytes/refusal classes; zero mapped execution"
    );
}
