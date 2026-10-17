//! B private SYNTHETIC unit harness. Added only to an isolated export under cfg(test).
//! Separate file Trust inputs are artificial unit anchors, never public authority.
use crate::{admission::Trust, component, wire};
use serde_json::{Value, json};
use std::collections::{BTreeMap, BTreeSet};

#[test]
#[ignore = "explicit isolated B synthetic job, Trust, and output paths required"]
fn private_component_probe() {
    let input = std::fs::read_to_string(std::env::var("B_COMPONENT_JOB").unwrap()).unwrap();
    let anchor: Value = serde_json::from_slice(
        &std::fs::read(std::env::var("B_COMPONENT_TRUST").unwrap()).unwrap(),
    )
    .unwrap();
    let trust = Trust {
        registry: anchor["registry"].as_str().unwrap().into(),
        profiles: BTreeMap::from([(
            anchor["profile"].as_str().unwrap().into(),
            BTreeSet::from([anchor["case"].as_str().unwrap().into()]),
        )]),
        engine: anchor["engine"].clone(),
    };
    let output = match component::execute(&input, &trust) {
        Ok(result) => json!({"outcome": "success", "result": result}),
        Err(error) => json!({"outcome": "refusal", "code": error.code,
                            "pointer": error.pointer, "message": error.message}),
    };
    std::fs::write(
        std::env::var("B_COMPONENT_OUTPUT").unwrap(),
        wire::canonical(&output).unwrap(),
    )
    .unwrap();
}
