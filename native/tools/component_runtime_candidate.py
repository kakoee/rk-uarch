"""Private installed-/3 build preparation. Never creates a selector or human authority.

Run from the repository venv with PYTHONPATH=.:src:contract. Fresh output is mandatory.
Build commands reuse the accepted offline container wrapper; trust/identities are additive.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import sysconfig
import tarfile
from copy import deepcopy
from pathlib import Path

from uarch_contract.hashing import canonical_json, content_hash, sha256

from rkuarch.engines.native.component_records import ComponentBuildInputs, ComponentBuildTrust
from rkuarch.engines.native.records import ToolInputs

ROOT = Path(__file__).resolve().parents[2]
B = "docs/reviews/U4-B-component-runtime-preparation-v2"
OUTPUT = "private-component"
IMAGE = "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value))


def binding(root: Path, path: Path) -> dict:
    return {"path": str(path.relative_to(root)), "byte_hash": sha256(path.read_bytes())}


def wrapper(root: Path = ROOT):
    path = root / "native/tools/component_candidate.py"
    spec = importlib.util.spec_from_file_location("accepted_component_wrapper", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def focused_ids(selection: dict) -> list[str]:
    """Exact B final affected plan: 27 positives and 20 finite D3 definitions."""
    plan = json.loads(
        (
            ROOT / "docs/reviews/U4-B-component-runtime-preparation-v1/private-final-plan.json"
        ).read_bytes()
    )
    ids = plan["cases"]
    assert set(ids) <= {row["case_id"] for row in selection["rows"]}
    return ids


def freeze(source: Path, commit: str) -> dict:
    """Freeze from an already verified clean tracked export, before generated identity."""
    from validation.component.runtime_selection import definitions

    selected = definitions()
    assert selected["selection"] == json.loads((source / B / "selection.json").read_bytes())
    out = source / OUTPUT
    out.mkdir(exist_ok=False)
    write(out / "selection.json", selected["selection"])
    ids = focused_ids(selected["selection"])
    write(out / "affected-selection.json", {"ids": ids, "scope": "private affected subset only"})
    jobs = selected["jobs"]
    registry = next(iter(jobs.values()))["job"]["registry"]
    write(out / "registry.json", registry)
    profiles = []
    for row in selected["selection"]["rows"]:
        if row["expected_layer"] == "result":
            path = out / "profiles" / (row["profile"]["profile_hash"].split(":")[1] + ".json")
            write(path, row["profile"])
            profiles.append(binding(source, path))
    profiles = sorted(profiles, key=lambda x: x["path"])
    trust = ComponentBuildTrust.model_validate(
        {
            "format": "uarch-component-build-trust/2",
            "purpose": "private-synthetic-tests-only",
            "semantics_file": binding(
                source, source / "docs/decisions/U0011-the-native-engine-core.md"
            ),
            "registry_hash": registry["registry_hash"],
            "registry_file": binding(source, out / "registry.json"),
            "profiles": profiles,
            "selection": binding(source, out / "selection.json"),
        }
    )
    write(out / "BuildTrust.json", trust)
    tool_path = source / "docs/reviews/U4-A-K2-construction-v1/candidate-04/ToolInputs.json"
    tools = ToolInputs.model_validate_json(tool_path.read_bytes())
    assert tools.image_digest == IMAGE
    paths = []
    for parent in ("native", "src/rkuarch", "contract/uarch_contract", "validation"):
        paths.extend(
            p
            for p in (source / parent).rglob("*")
            if p.is_file()
            and p.suffix in (".rs", ".toml", ".lock", ".py", ".json")
            and "generated" not in p.parts
        )
    paths += [source / name for name in ("pyproject.toml", "uv.lock")]
    paths += [
        source / "docs/reviews/U4-A-K2-construction-v1/inputs" / n
        for n in ("rustc-wrapper.sh", "linker.sh")
    ]
    inventory = [
        {**binding(source, p), "role": "rust" if p.suffix == ".rs" else "config"}
        for p in sorted(set(paths))
    ]
    model = [x for x in inventory if x["path"].startswith("native/crates/uarch-engine/src/")]
    build = ComponentBuildInputs.model_validate(
        {
            "format": "uarch-component-build-inputs/2",
            "source_commit": commit,
            "source_files": inventory,
            "trust_hash": content_hash(trust),
            "trust_file": binding(source, out / "BuildTrust.json"),
            "tool_inputs_hash": content_hash(tools),
            "tool_inputs_file": binding(source, tool_path),
            "model_source_paths": [x["path"] for x in model],
            "model_inputs_hash": content_hash(model),
            "mode_configs": [
                {
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
                    ]
                    + (["--release"] if mode == "release" else []),
                    "rustflags": tools.flags,
                }
                for mode in ("debug", "release")
            ],
            "generated_identity_output_paths": ["native/crates/uarch-engine/generated/identity.rs"],
            "permitted_environment": {
                "CARGO_HOME": "/cargo-home",
                "CARGO_NET_OFFLINE": "true",
                "CARGO_TARGET_DIR": "/target",
                "RUSTUP_AUTO_INSTALL": "0",
                "LC_ALL": "C",
            },
        }
    )
    write(out / "BuildInputs.json", build)
    engine = {
        "name": "native",
        "version": "native-stage/1",
        "implementation_hash": content_hash(build),
        "compiler_lock_hash": content_hash(tools),
        "model": {
            "name": "native-intervals",
            "version": "2",
            "implementation_hash": build.model_inputs_hash,
        },
    }
    write(out / "engine.json", engine)
    generated = source / build.generated_identity_output_paths[0]
    generated.parent.mkdir(exist_ok=True)
    generated.write_text(
        'pub const ENGINE_JSON: &str = r###"'
        + canonical_json(engine)
        + '"###;\npub const TRUST_JSON: &str = r###"'
        + canonical_json(trust)
        + '"###;\n'
    )
    transitions, positive = [], []
    for name, item in jobs.items():
        job = deepcopy(item["job"])
        old_hash = job["job_hash"]
        job["engine"] = engine
        job["job_hash"] = content_hash(job, exclude=("job_hash",))
        path = out / "jobs" / (name + ".json")
        write(path, job)
        if name in ids:
            write(out / "affected-inputs" / path.name, job)
        transitions.append(
            {
                "case_id": name,
                "definition_job_hash": old_hash,
                "private_build_job_hash": job["job_hash"],
                "file": binding(source, path),
            }
        )
        if item["item"]["expected_layer"] == "result":
            positive.append(
                {
                    "case_id": name,
                    "job_hash": job["job_hash"],
                    "profile_hash": job["admission"]["profile_hash"],
                    "file": binding(source, path),
                }
            )
    write(out / "job-transitions.json", transitions)
    write(out / "positive-inventory.json", positive)
    expected = json.loads(
        (source / "docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json").read_bytes()
    )
    write(out / "observation-contract.json", expected["observation_contract"])
    return engine


def prepare(out: Path) -> None:
    if not out.is_absolute() or not out.is_relative_to(Path("/tmp")):
        raise ValueError("fresh private absolute /tmp output required")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT):
        raise ValueError("clean committed freeze required")
    out.mkdir(exist_ok=False)
    for name in ("source", "commands", "docker-config", "controls"):
        (out / name).mkdir()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    archive = out / "source.tar"
    subprocess.run(["git", "archive", "-o", str(archive), commit], cwd=ROOT, check=True)
    with tarfile.open(archive) as tar:
        tar.extractall(out / "source", filter="data")
    c = wrapper()
    accepted = json.loads(c.CACHE_RECORD.read_bytes())
    cache = Path(accepted["private_root"])
    assert c.inventory(cache) == accepted["files"]
    shutil.copytree(cache, out / "cache")
    assert c.inventory(out / "cache") == accepted["files"]
    for n in ("rustc-wrapper.sh", "linker.sh"):
        shutil.copy2(ROOT / "docs/reviews/U4-A-K2-construction-v1/inputs" / n, out / "controls" / n)
        (out / "controls" / n).chmod(0o555)
    assert (
        c.command(
            out,
            "image",
            [
                "/usr/bin/docker",
                "--host",
                "unix:///var/run/docker.sock",
                "image",
                "inspect",
                IMAGE,
                "--format",
                "{{.Id}} {{.Os}} {{.Architecture}}",
            ],
        )
        == 0
    )
    assert (out / "commands/image.stdout").read_text().strip() == IMAGE + " linux amd64"
    engine = freeze(out / "source", commit)
    write(
        out / "preparation.json",
        {
            "source_commit": commit,
            "source_archive": binding(out, archive),
            "engine": engine,
            "image": IMAGE,
            "cache_files": len(accepted["files"]),
            "authority": None,
            "wrapper": binding(ROOT, ROOT / "native/tools/component_candidate.py"),
        },
    )
    for tool, argv in (
        ("rustc", [c.BIN + "rustc", "-vV"]),
        ("cargo", [c.BIN + "cargo", "-vV"]),
        ("rustfmt", [c.BIN + "rustfmt", "--version"]),
        ("clippy", [c.BIN + "clippy-driver", "--version"]),
        ("cargo-deny", ["/usr/local/cargo/bin/cargo-deny", "--version"]),
    ):
        assert c.command(out, "tool-" + tool, c.docker(out, "debug", "tool-" + tool) + argv) == 0
        assert (out / "commands" / ("tool-" + tool + ".stdout")).read_bytes() == (
            ROOT / "docs/reviews/U4-A-K2-C1-precise-v1" / (tool + ".stdout")
        ).read_bytes()


def verify(out: Path) -> None:
    source = out / "source"
    build = ComponentBuildInputs.model_validate_json(
        (source / OUTPUT / "BuildInputs.json").read_bytes()
    )
    for f in build.source_files:
        assert sha256((source / f.path).read_bytes()) == f.byte_hash, f.path
    for f in (build.trust_file, build.tool_inputs_file):
        assert sha256((source / f.path).read_bytes()) == f.byte_hash
    engine = json.loads((source / OUTPUT / "engine.json").read_bytes())
    assert engine["implementation_hash"] == content_hash(build)
    generated = source / build.generated_identity_output_paths[0]
    trust = json.loads((source / build.trust_file.path).read_bytes())
    assert generated.read_text() == (
        'pub const ENGINE_JSON: &str = r###"'
        + canonical_json(engine)
        + '"###;\npub const TRUST_JSON: &str = r###"'
        + canonical_json(trust)
        + '"###;\n'
    )


def build(out: Path, mode: str) -> None:
    """Actual construction recipe; invoke the frozen export's copy of this tool."""
    source = out / "source"
    if ROOT.resolve() != source.resolve():
        raise ValueError("build must use the exact frozen export recipe")
    verify(out)
    c = wrapper(source)
    inputs = ComponentBuildInputs.model_validate_json(
        (source / OUTPUT / "BuildInputs.json").read_bytes()
    )
    config = next(x for x in inputs.mode_configs if x.mode == mode)
    command = c.docker(out, mode, mode + "-build") + [
        c.BIN + "cargo",
        *config.cargo_args,
        "--",
        "-C",
        "link-arg=-Wl,-Map=/receipts/" + mode + ".map",
    ]
    if c.command(out, mode + "-build", command):
        raise ValueError("private production executable construction failed")
    test = [
        c.BIN + "cargo",
        "test",
        "--offline",
        "--locked",
        "-p",
        "uarch-engine",
        "--lib",
        "--no-run",
        "--message-format=json",
    ] + (["--release"] if mode == "release" else [])
    if c.command(out, mode + "-test-build", c.docker(out, mode, mode + "-test-build") + test):
        raise ValueError("private unit executable construction failed")
    verify(out)
    if c.inventory(out / "cache") != json.loads(c.CACHE_RECORD.read_bytes())["files"]:
        raise ValueError("accepted private cache changed")


def imports(root: Path, observation_root: Path | None = None) -> dict:
    """Full project Python closure and stdlib/accepted dependency bytes, not caller modules."""
    files = sorted(
        {
            p
            for d in ("src/rkuarch", "contract/uarch_contract", "validation")
            for p in (root / d).rglob("*.py")
        }
    )
    external = set()
    stdlib = Path(sysconfig.get_path("stdlib"))
    external.update(p.resolve() for p in stdlib.rglob("*.py") if "site-packages" not in p.parts)
    external.update(p.resolve() for p in (stdlib / "lib-dynload").glob("*.so"))
    for name in (
        "pydantic",
        "pydantic_core",
        "annotated_types",
        "typing_extensions",
        "typing_inspection",
        "yaml",
    ):
        spec = importlib.util.find_spec(name)
        p = Path(spec.origin).resolve()
        external.add(p)
        if spec.submodule_search_locations:
            external.update(x.resolve() for x in p.parent.rglob("*") if x.suffix in (".py", ".so"))
    return {
        "checker": "validation.component.observations_v3:check_v3",
        "observations": "uarch-native-observations/3",
        "import_root": str(root),
        "files": [binding(root, p) for p in files],
        "external_files": [binding(Path("/"), p) for p in sorted(external)],
        "python_executable": binding(Path("/"), Path(sys.executable).resolve()),
        "independent_binding": binding(
            root,
            root
            / "docs/reviews/U4-A-component-runtime-stage2-v1/final-join-v2/consumer-bindings.json",
        ),
        "observation_contract": binding(
            observation_root or root,
            (observation_root or root) / OUTPUT / "observation-contract.json",
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "verify", "build"))
    parser.add_argument("output", type=Path)
    parser.add_argument("--mode", choices=("debug", "release"), default="debug")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.output)
    elif args.action == "build":
        build(args.output, args.mode)
    else:
        verify(args.output)


if __name__ == "__main__":
    main()
