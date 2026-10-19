"""Explicit production construction specification; pure data, never execution authority."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import model_validator
from uarch_contract.common import FrozenModel

BIN = "/usr/local/rustup/toolchains/1.99.0-x86_64-unknown-linux-gnu/bin/"
CARGO = BIN + "cargo"
FLAGS = ("-C", "debuginfo=1", "-C", "linker=/controls/linker.sh")


def mode_spec(mode: str) -> dict[str, Any]:
    if mode not in ("debug", "release"):
        raise ValueError("explicit production construction mode")
    return {
        "mode": mode,
        "cargo_args": [
            "rustc",
            "--offline",
            "--locked",
            "-p",
            "uarch-engine",
            "--bin",
            "uarch-engine",
            "-vv",
            "--message-format=json",
            *(["--release"] if mode == "release" else []),
            "--",
            "-C",
            f"link-arg=-Wl,-Map=/receipts/{mode}.map",
        ],
        "rustflags": list(FLAGS),
        "permitted_environment": {
            "PATH": BIN + ":/usr/local/cargo/bin:/usr/bin:/bin",
            "CARGO_HOME": "/cargo-home",
            "CARGO_NET_OFFLINE": "true",
            "CARGO_TARGET_DIR": "/target",
            "CARGO_REGISTRIES_CRATES_IO_PROTOCOL": "sparse",
            "RUSTUP_AUTO_INSTALL": "0",
            "LC_ALL": "C",
            "RUSTC": BIN + "rustc",
            "RUSTC_WRAPPER": "/controls/rustc-wrapper.sh",
            "RUSTFLAGS": " ".join(FLAGS),
            "C2_RUN_TAG": mode + "-build",
        },
    }


class ConstructionMode(FrozenModel):
    mode: Literal["debug", "release"]
    cargo_args: tuple[str, ...]
    rustflags: tuple[str, ...]
    permitted_environment: dict[str, str]

    @model_validator(mode="after")
    def exact(self) -> ConstructionMode:
        if self.model_dump(mode="json") != mode_spec(self.mode):
            raise ValueError("exact production construction specification required")
        return self


def construction_modes(flags: tuple[str, ...] | list[str]) -> list[dict[str, Any]]:
    if tuple(flags) != FLAGS:
        raise ValueError("accepted construction flags required")
    return [mode_spec(mode) for mode in ("debug", "release")]


def selected_mode(modes: list[dict[str, Any]], mode: str) -> ConstructionMode:
    parsed = [ConstructionMode.model_validate(value) for value in modes]
    if [value.mode for value in parsed] != ["debug", "release"]:
        raise ValueError("exact ordered debug/release construction modes required")
    if mode not in ("debug", "release"):
        raise ValueError("explicit production construction mode")
    return next(value for value in parsed if value.mode == mode)


def invocation(modes: list[dict[str, Any]], mode: str) -> tuple[list[str], dict[str, str]]:
    value = selected_mode(modes, mode)
    return [CARGO, *value.cargo_args], dict(value.permitted_environment)
