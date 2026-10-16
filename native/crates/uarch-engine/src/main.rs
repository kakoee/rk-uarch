//! Fixed-delay public process boundary; one request, no discovery or engine selectors.
#![forbid(unsafe_code)]
use std::io::{Read, Write};
use uarch_engine::protocol::{MAX_INPUT_BYTES, error_bytes, respond};
fn main() {
    let args: Vec<_> = std::env::args_os().skip(1).collect();
    if args != ["--protocol", "uarch-engine/3"] {
        let error = uarch_engine::Refusal {
            code: "UnsupportedProtocol",
            message: "expected --protocol uarch-engine/3".into(),
            pointer: "/protocol".into(),
        };
        if std::io::stderr().write_all(&error_bytes(&error)).is_err() {
            std::process::exit(1);
        }
        std::process::exit(2);
    }
    let mut input = Vec::new();
    if std::io::stdin()
        .take((MAX_INPUT_BYTES + 1) as u64)
        .read_to_end(&mut input)
        .is_err()
    {
        std::process::exit(1);
    }
    match respond(&input) {
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
