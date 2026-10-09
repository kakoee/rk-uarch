"""Review-only U2 input staging and semantic audits; never invokes an oracle.

The files are existing shared carriers plus a tooling inventory, not a new runtime schema.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, NamedTuple

import yaml
from uarch_contract.exports import ComponentPrecision, ExecutionModelInput
from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import artifact_identity, content_hash, strict_json_loads

from rkuarch.hw.export import export_component, project_for_oracle
from scripts import vendor_rk as vendor

ROOT = Path(__file__).resolve().parents[1]
ADOPTED = ROOT / "contract/vendor" / ("rk-sim@" + vendor.PIN)
ADOPTED_MANIFEST = vendor.HISTORICAL_MANIFEST_SHA256


class Inputs(NamedTuple):
    root: Path
    entries: tuple[ComponentPrecision, ...]
    descriptors: dict[str, bytes]
    artifacts: dict[str, Any]
    matrix: dict[str, tuple[dict[str, str], ...]]
    models: tuple[dict[str, Any], ...]
    manifest_sha256: str


def role(entry: ComponentPrecision) -> str:
    return (
        Path(entry.binding.component_file).name
        if entry.binding.kind == "upstream_only"
        else "npu-l4.yaml"
    )


def support_files() -> tuple[Path, ...]:
    paths = {ROOT / "pyproject.toml", ROOT / "uv.lock", ROOT / "hw/designs/npu-l4.yaml"}
    paths.update(vendor.retained_provenance_root().rglob("*"))
    for directory in ("src/rkuarch", "contract/uarch_contract", "scripts"):
        paths.update((ROOT / directory).rglob("*.py"))
    paths.update(
        ROOT / p
        for p in (
            "contract/tests/nominal_candidate.py",
            "contract/tests/parity.py",
            "contract/tests/u2_prepared_adapter.py",
            "tests/u2_comparison.py",
            "tests/u2_refresh.py",
            "tests/fixtures/u2_b/refresh/pinned-source-sha256.json",
            "tests/fixtures/u2_b/refresh/pinned-compute.py.txt",
            "tests/fixtures/u2_b/refresh/pinned-engine-orchestrator.py.txt",
            "tests/fixtures/u2_b/refresh/pinned-components-loader.py.txt",
            "contract/tests/u2_comparison.py",
        )
    )
    return tuple(sorted(p for p in paths if p.is_file()))


def prepare_inputs(destination: Path) -> str:
    """Copy exact accepted inputs; replay A's pure export for equality; no upstream calls."""
    if any(p.is_symlink() for p in (destination, *destination.parents)):
        raise ValueError("input destination symlink ancestor")
    if destination.exists() or destination.is_symlink():
        raise ValueError("input destination must be absent")
    historical = vendor.retained_provenance()
    directory = ROOT / "contract/tests/fixtures/u2_b"
    export = directory / "a2-export"
    entries = strict_json_loads((directory / "component-precisions.json").read_bytes())
    artifacts = {}
    for path in list(export.glob("*.json")) + [
        directory / "asic_placeholder-execution.json",
        directory / "nvidia_h100_sxm-execution.json",
    ]:
        value = strict_json_loads(path.read_bytes())
        artifacts[artifact_identity(value)] = value
    binding = strict_json_loads((export / "npu-l4.binding.json").read_bytes())
    h1 = dict(
        format="uarch-component-precision/1",
        component_id=binding["component_id"],
        binding=binding,
        precisions=[dict(compute="bf16", kv_cache="bf16")],
    )
    h1["precision_hash"] = content_hash(h1)
    entries.append(h1)
    execution = ExecutionModelInput.model_validate(artifacts[binding["execution_model_hash"]])
    hardware = HardwareSpec.model_validate(
        yaml.safe_load((ROOT / "hw/designs/npu-l4.yaml").read_bytes())
    )
    truth, derivation = export_component(hardware, execution, component_id=h1["component_id"])
    raw, actual_binding = project_for_oracle(
        hardware, truth, derivation, execution, upstream_sha=vendor.PIN
    )
    if (
        raw != (export / "npu-l4.oracle-compat.yaml").read_bytes()
        or actual_binding.model_dump(mode="json") != binding
        or truth.model_dump(mode="json") != artifacts[binding["primary_export_hash"]]
    ):
        raise ValueError("actual A export differs from reviewed input")
    descriptors = {
        e["component_id"]: historical[e["binding"]["component_file"]] for e in entries[:-1]
    }
    descriptors[h1["component_id"]] = raw
    validated = vendor.validate_u2_component_inputs(entries, descriptors, artifacts)
    files = {"component-precisions.json": vendor.canonical(entries)}
    for entry in validated:
        files["components/" + role(entry)] = descriptors[entry.component_id]
        artifacts[entry.binding.binding_hash] = entry.binding.model_dump(mode="json")
    for identity, value in artifacts.items():
        files["artifacts/" + identity[7:] + ".json"] = vendor.canonical(value)
    for name, data in historical.items():
        files["historical-source/" + name] = data
        if name.startswith("model_shapes/"):
            files[name] = data
    files["support-files.json"] = vendor.canonical(
        {str(p.relative_to(ROOT)): vendor.digest(p.read_bytes()) for p in support_files()}
    )
    files["PIN"] = (vendor.PIN + "\n").encode()
    files["ADOPTED-MANIFEST-SHA256"] = (ADOPTED_MANIFEST + "\n").encode()
    manifest = "".join(
        vendor.digest(data) + "  " + name + "\n" for name, data in sorted(files.items())
    ).encode()
    destination.mkdir(parents=True)
    for name, data in files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (destination / "SHA256SUMS").write_bytes(manifest)
    return vendor.digest(manifest)


def load_inputs(directory: Path, expected_manifest: str, *, check_support: bool = True) -> Inputs:
    """Verify exact files and frozen hashes before returning accepted existing carriers."""
    for path in (directory, *directory.parents):
        if path.is_symlink():
            raise ValueError("input symlink ancestor")
    manifest = (directory / "SHA256SUMS").read_bytes()
    if vendor.digest(manifest) != expected_manifest:
        raise ValueError("input manifest changed")
    named = {}
    for line in manifest.decode().splitlines():
        digest, name = line.split("  ", 1)
        if not vendor.safe_path(name) or name in named:
            raise ValueError("input path/inventory")
        named[name] = digest
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
    if actual != set(named) | {"SHA256SUMS"}:
        raise ValueError("input inventory changed")
    for name, digest in named.items():
        path = directory / name
        if (
            any(p.is_symlink() for p in (path, *path.parents))
            or vendor.digest(path.read_bytes()) != digest
        ):
            raise ValueError("input bytes changed: " + name)
    if (directory / "PIN").read_text().strip() != vendor.PIN:
        raise ValueError("input pin")
    if (directory / "ADOPTED-MANIFEST-SHA256").read_text().strip() != ADOPTED_MANIFEST:
        raise ValueError("input adopted identity")
    if check_support:
        support = strict_json_loads((directory / "support-files.json").read_bytes())
        if set(support) != {p.relative_to(ROOT).as_posix() for p in support_files()}:
            raise ValueError("input support inventory changed")
        for name, digest in support.items():
            if not vendor.safe_path(name) or vendor.digest((ROOT / name).read_bytes()) != digest:
                raise ValueError("input support changed: " + name)
    entries = strict_json_loads((directory / "component-precisions.json").read_bytes())
    descriptors = {
        e["component_id"]: (
            directory / "components" / role(ComponentPrecision.model_validate(e))
        ).read_bytes()
        for e in entries
    }
    artifacts = {
        artifact_identity(v): v
        for p in sorted((directory / "artifacts").glob("*.json"))
        for v in [strict_json_loads(p.read_bytes())]
    }
    for path in (directory / "artifacts").glob("*.json"):
        identity = artifact_identity(strict_json_loads(path.read_bytes()))
        if path.stem != identity[7:]:
            raise ValueError("input artifact filename/identity differs")
    historical = vendor.retained_provenance(directory / "historical-source")
    typed = vendor.validate_u2_component_inputs(
        entries, descriptors, artifacts, provenance_root=directory / "historical-source"
    )
    matrix = {role(e): tuple(p.model_dump(mode="json") for p in e.precisions) for e in typed}
    models = tuple(
        strict_json_loads(p.read_bytes())
        for p in sorted((directory / "model_shapes").glob("*.json"))
    )
    old = {
        Path(name).name: data
        for name, data in historical.items()
        if name.startswith("model_shapes/")
    }
    if {p.name: p.read_bytes() for p in (directory / "model_shapes").glob("*.json")} != old:
        raise ValueError("input retained sidecars/attribution changed")
    return Inputs(directory, typed, descriptors, artifacts, matrix, models, expected_manifest)


def semantic_rows(old: list[dict[str, Any]], new: list[dict[str, Any]]) -> dict[str, Any]:
    def index(rows: list[dict[str, Any]]) -> dict[str, Any]:
        result = {}
        for row in rows:
            key = json.dumps(
                [row[k] for k in ("component_params_file", "model_id", "precision", "tp", "query")],
                sort_keys=True,
            )
            if key in result:
                raise ValueError("duplicate semantic query identity")
            result[key] = row
        return result

    a, b = index(old), index(new)
    return dict(
        added=[b[k] for k in sorted(b.keys() - a.keys())],
        removed=[a[k] for k in sorted(a.keys() - b.keys())],
        changed=[
            dict(key=k, before=a[k], after=b[k])
            for k in sorted(a.keys() & b.keys())
            if a[k] != b[k]
        ],
        unchanged=sum(a[k] == b[k] for k in a.keys() & b.keys()),
    )


def compare_snapshots(old: Path, new: Path) -> dict[str, Any]:
    """Supplementary complete semantic/byte audit; never substitutes for strict validation."""
    vendor.check_manifest(old)
    vendor.check_manifest(new)
    a = {p.relative_to(old).as_posix(): p.read_bytes() for p in old.rglob("*") if p.is_file()}
    b = {p.relative_to(new).as_posix(): p.read_bytes() for p in new.rglob("*") if p.is_file()}
    return dict(
        old_manifest_sha256=vendor.digest(a["MANIFEST.json"]),
        new_manifest_sha256=vendor.digest(b["MANIFEST.json"]),
        files=[
            dict(
                path=k,
                before_sha256=vendor.digest(a[k]) if k in a else None,
                after_sha256=vendor.digest(b[k]) if k in b else None,
            )
            for k in sorted(a.keys() | b.keys())
            if a.get(k) != b.get(k)
        ],
        semantic_files=[
            dict(
                path=k,
                before=strict_json_loads(a[k]) if k in a else None,
                after=strict_json_loads(b[k]) if k in b else None,
            )
            for k in sorted(a.keys() | b.keys())
            if k.endswith(".json")
            and k not in ("parity/fixtures.json", "parity/refusals.json")
            and a.get(k) != b.get(k)
        ],
        descriptors=[
            dict(
                path=k,
                before=yaml.safe_load(a[k]) if k in a else None,
                after=yaml.safe_load(b[k]) if k in b else None,
            )
            for k in sorted(a.keys() | b.keys())
            if k.endswith(".yaml") and a.get(k) != b.get(k)
        ],
        rows=semantic_rows(
            json.loads(a["parity/fixtures.json"]), json.loads(b["parity/fixtures.json"])
        ),
        refusals=dict(
            before=json.loads(a["parity/refusals.json"]),
            after=json.loads(b["parity/refusals.json"]),
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("destination", type=Path)
    verify = sub.add_parser("verify")
    verify.add_argument("directory", type=Path)
    verify.add_argument("manifest")
    compare = sub.add_parser("compare")
    compare.add_argument("old", type=Path)
    compare.add_argument("new", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        print(prepare_inputs(args.destination))
    elif args.command == "verify":
        print(
            "verified",
            len(load_inputs(args.directory, args.manifest).entries),
            "explicit components",
        )
    else:
        print(json.dumps(compare_snapshots(args.old, args.new), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
