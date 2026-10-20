//! Normal cargo-test coverage of the shipping /4 executable; synthetic inputs only.
use serde_json::Value;
use std::io::Write;
use std::process::{Command, Stdio};

fn invoke(input: &[u8], test_only: bool) -> std::process::Output {
    let mut command = Command::new(env!("CARGO_BIN_EXE_uarch-engine"));
    command.args(["--protocol", "uarch-engine/4"]);
    if test_only {
        command.arg("--test-only");
    }
    let mut child = command
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.take().unwrap().write_all(input).unwrap();
    child.wait_with_output().unwrap()
}

#[test]
fn ordinary_production_and_fixture_are_deterministic() {
    for (input, fixture, duration) in [
        (
            include_bytes!("data/ordinary-production.json").as_slice(),
            false,
            656000,
        ),
        (
            include_bytes!("data/ordinary-fixture.json").as_slice(),
            true,
            121000,
        ),
    ] {
        let first = invoke(input, fixture);
        assert!(first.status.success(), "{:?}", first);
        assert!(first.stderr.is_empty());
        let result: Value = serde_json::from_slice(&first.stdout).unwrap();
        assert_eq!(result["protocol"], "uarch-engine/4");
        assert_eq!(result["duration_ps"], duration);
        assert_eq!(first.stdout, invoke(input, fixture).stdout);
        let mismatch = invoke(input, !fixture);
        assert_eq!(mismatch.status.code(), Some(2));
        assert!(mismatch.stdout.is_empty());
        let refusal: Value = serde_json::from_slice(&mismatch.stderr).unwrap();
        assert_eq!(refusal["code"], "AdmissionMismatch");
    }
}

#[test]
fn ordinary_protocol_and_json_refusals() {
    for (input, code) in [
        (b"{}".as_slice(), "UnsupportedProtocol"),
        (b"{", "InvalidJson"),
    ] {
        let result = invoke(input, false);
        assert_eq!(result.status.code(), Some(2));
        assert!(result.stdout.is_empty());
        let refusal: Value = serde_json::from_slice(&result.stderr).unwrap();
        assert_eq!(refusal["code"], code);
    }
}
