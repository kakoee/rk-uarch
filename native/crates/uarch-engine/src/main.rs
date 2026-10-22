//! Ordinary component process boundary: one EOF JSON request.
#![forbid(unsafe_code)]
use std::io::{Read, Write};
use uarch_engine::protocol::{
    MAX_INPUT_BYTES, MAX_REFERENCE_INPUT_BYTES, error_bytes, respond_for_protocol,
};
fn main() {
    let args: Vec<_> = std::env::args_os().skip(1).collect();
    let test_only = args == ["--protocol", "uarch-engine/4", "--test-only"]
        || args == ["--protocol", "uarch-engine/5", "--test-only"];
    if !test_only
        && args != ["--protocol", "uarch-engine/4"]
        && args != ["--protocol", "uarch-engine/5"]
    {
        let error = uarch_engine::Refusal {
            code: "UnsupportedProtocol",
            message: "expected --protocol uarch-engine/4 or uarch-engine/5 [--test-only]".into(),
            pointer: "/protocol".into(),
        };
        if std::io::stderr().write_all(&error_bytes(&error)).is_err() {
            std::process::exit(1);
        }
        std::process::exit(2);
    }
    let mut input = Vec::new();
    if std::io::stdin()
        .take(
            (if args.get(1).is_some_and(|x| x == "uarch-engine/5") {
                MAX_REFERENCE_INPUT_BYTES
            } else {
                MAX_INPUT_BYTES
            } + 1) as u64,
        )
        .read_to_end(&mut input)
        .is_err()
    {
        std::process::exit(1);
    }
    match respond_for_protocol(&input, test_only, args[1].to_str()) {
        Ok(output) => {
            if std::io::stdout().write_all(&output).is_err() {
                std::process::exit(1);
            }
        }
        Err(error) => {
            if error.code == "InternalError" {
                std::process::exit(1);
            }
            if std::io::stderr().write_all(&error_bytes(&error)).is_err() {
                std::process::exit(1);
            }
            std::process::exit(2);
        }
    }
}
