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
from types import ModuleType
from typing import Any

from uarch_contract.hashing import canonical_json, content_hash, sha256

from rkuarch.engines.native.component_construction import construction_modes, invocation
from rkuarch.engines.native.component_records import (
    ComponentBuildInputsV3,
    ComponentBuildTrust,
    parse_component_build_inputs,
)
from rkuarch.engines.native.records import ToolInputs

ROOT = Path(__file__).resolve().parents[2]
B = "docs/reviews/U4-B-component-runtime-preparation-v2"
OUTPUT = "private-component"
IMAGE = "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value))


def binding(root: Path, path: Path) -> dict[str, Any]:
    return {"path": str(path.relative_to(root)), "byte_hash": sha256(path.read_bytes())}


def wrapper(root: Path = ROOT) -> ModuleType:
    path = root / "native/tools/component_candidate.py"
    spec = importlib.util.spec_from_file_location("accepted_component_wrapper", path)
    if spec is None or spec.loader is None:
        raise ValueError("component wrapper source loader required")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def focused_ids(selection: dict[str, Any]) -> list[str]:
    """Exact B final affected plan: 27 positives and 20 finite D3 definitions."""
    plan = json.loads(
        (
            ROOT / "docs/reviews/U4-B-component-runtime-preparation-v1/private-final-plan.json"
        ).read_bytes()
    )
    ids: list[str] = plan["cases"]
    assert set(ids) <= {row["case_id"] for row in selection["rows"]}
    return ids


def freeze(source: Path, commit: str) -> dict[str, Any]:
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
    paths: list[Path] = []
    for parent in ("native", "src/rkuarch", "contract/uarch_contract", "validation"):
        paths.extend(
            p
            for p in (source / parent).rglob("*")
            if p.is_file()
            and p.suffix in (".rs", ".toml", ".lock", ".py", ".json")
            and "generated" not in p.parts
        )
    paths += [source / name for name in ("pyproject.toml", "uv.lock")]
    paths.append(source / "docs/reviews/U4-B-K2-construction-audit-v1/trace_canary.py")
    paths += [
        source / "docs/reviews/U4-B-K2-parallel-first-use-v1" / name
        for name in ("parallel_core.py", "resource_limits.py")
    ]
    paths += [
        source / "docs/reviews/U4-A-K2-construction-v1/inputs" / n
        for n in ("rustc-wrapper.sh", "linker.sh")
    ]
    inventory = [
        {**binding(source, p), "role": "rust" if p.suffix == ".rs" else "config"}
        for p in sorted(set(paths))
    ]
    model = [x for x in inventory if x["path"].startswith("native/crates/uarch-engine/src/")]
    build = ComponentBuildInputsV3.model_validate(
        {
            "format": "uarch-component-build-inputs/3",
            "source_commit": commit,
            "source_files": inventory,
            "trust_hash": content_hash(trust),
            "trust_file": binding(source, out / "BuildTrust.json"),
            "tool_inputs_hash": content_hash(tools),
            "tool_inputs_file": binding(source, tool_path),
            "model_source_paths": [x["path"] for x in model],
            "model_inputs_hash": content_hash(model),
            "mode_configs": construction_modes(tools.flags),
            "generated_identity_output_paths": ["native/crates/uarch-engine/generated/identity.rs"],
        }
    )
    write(out / "BuildInputs.json", build)
    write(
        out / "ordinary-build-recipe.json",
        ordinary_recipe((out / "BuildInputs.json").read_bytes()),
    )
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
    (out / "source-commit.raw").write_bytes(
        subprocess.check_output(["git", "cat-file", "commit", commit], cwd=ROOT)
    )
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


def verify(out: Path) -> None:
    source = out / "source"
    build = parse_component_build_inputs(
        json.loads((source / OUTPUT / "BuildInputs.json").read_bytes())
    )
    for f in build.source_files:
        assert sha256((source / f.path).read_bytes()) == f.byte_hash, f.path
    for file in (build.trust_file, build.tool_inputs_file):
        assert sha256((source / file.path).read_bytes()) == file.byte_hash
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


def construction_recipe(build_input_bytes: bytes) -> dict[str, Any]:
    """Bind exact /3 input bytes without inventing values or executing a build."""
    build = ComponentBuildInputsV3.model_validate_json(build_input_bytes)
    sources = [
        value
        for value in build.source_files
        if value.path == "native/tools/component_runtime_candidate.py"
    ]
    if len(sources) != 1:
        raise ValueError("exact preparation source required for construction recipe")
    return {
        "format": "component-capture-recipe/2",
        "source_commit": build.source_commit,
        "build_inputs_byte_hash": sha256(build_input_bytes),
        "preparation_source": sources[0].model_dump(mode="json"),
        "mode_configs": [value.model_dump(mode="json") for value in build.mode_configs],
        "generated_identity_output_paths": list(build.generated_identity_output_paths),
    }


def production_invocation(
    inputs: ComponentBuildInputsV3, mode: str
) -> tuple[list[str], dict[str, str]]:
    """Pure rendering of the exact declared production command, with no appended args."""
    checked = ComponentBuildInputsV3.model_validate(inputs.model_dump(mode="json"))
    return invocation([value.model_dump(mode="json") for value in checked.mode_configs], mode)


def ordinary_recipe(build_input_bytes: bytes) -> dict[str, Any]:
    """Finite ordinary declaration; optional historical capture is a separate API."""
    result = construction_recipe(build_input_bytes)
    result["format"] = "component-ordinary-build-recipe/1"
    result["optional_construction_reads"] = "not-required"
    result["startup_assurance"] = "separate-required-public-gate"
    return result


def build(out: Path, mode: str, build_root: Path) -> None:
    """Later ordinary construction through B's harness and the bounded guardian.

    No unit-test compilation is hidden in this production command. Required scoped
    tests/clippy and independent review are separate retained obligations.
    """
    from native.tools.component_ordinary_build import construct

    if ROOT.resolve() != (out / "source").resolve():
        raise ValueError("build must use the exact frozen export recipe")
    verify(out)
    construct(out, build_root, mode, imports(out / "source"))
    verify(out)


def imports(root: Path, observation_root: Path | None = None) -> dict[str, Any]:
    """Full project Python closure and stdlib/accepted dependency bytes, not caller modules."""
    files = sorted(
        {
            p
            for d in ("src/rkuarch", "contract/uarch_contract", "validation", "native/tools")
            for p in (root / d).rglob("*.py")
        }
    )
    # Hash-checked runpy helpers are executable inputs, despite living under docs/.
    files.extend(
        root / "docs/reviews/U4-B-K2-parallel-first-use-v1" / name
        for name in ("parallel_core.py", "resource_limits.py")
    )
    files.append(root / "docs/reviews/U4-B-K2-construction-audit-v1/trace_canary.py")
    external: set[Path] = set()
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
        if spec is None or spec.origin is None:
            raise ValueError("accepted dependency origin required: " + name)
        p = Path(spec.origin).resolve()
        external.add(p)
        if spec.submodule_search_locations:
            external.update(x.resolve() for x in p.parent.rglob("*") if x.suffix in (".py", ".so"))
    return {
        "checker": "validation.component.observations_v3:check_v3",
        "observations": "uarch-native-observations/3",
        "import_root": str(root),
        "files": [binding(root, p) for p in sorted(set(files))],
        "external_files": [binding(Path("/"), p) for p in sorted(external)],
        "python_executable": binding(Path("/"), Path(sys.executable).resolve()),
        "independent_binding": binding(
            root,
            root
            / "docs/reviews/U4-A-build-provenance-final-v1"
            / "activation-consumer-bindings.json",
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
    parser.add_argument("--build-root", type=Path)
    parser.add_argument("--mode", choices=("debug", "release"), default="debug")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.output)
    elif args.action == "build":
        if args.build_root is None:
            parser.error("build requires an exclusive --build-root")
        build(args.output, args.mode, args.build_root)
    else:
        verify(args.output)


if __name__ == "__main__":
    main()
