"""Human-only snapshot writer; --check reads committed artifacts without rk-sim.

The subprocess bridge invokes the pinned project's own loader, accelerator adapter,
iteration_cost and IterationCounts. No workload arithmetic is implemented here.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shlex
import subprocess
import tempfile
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from uarch_contract.exports import ComponentPrecision

PIN = "1e5706e0ebfcc67c1a7333079a35b75f693e9963"
# Independently read at the pinned revision; CI needs no upstream checkout.
PINNED_UV_LOCK_SHA256 = "d984e55723326751ac3f888712f98462a525315ad4693691dbc3f2f5dc7f577c"
ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_MANIFEST_SHA256 = "b3a575d0e3f27a4057678a2298609a580fd5a5e1dd858b0f4af086f2dc9e0e1d"
SOURCES = (
    "rk/provenance.py",
    "rk/engine/f0/compute.py",
    "rk/engine/orchestrator.py",
    "rk/components/loader.py",
    *(
        f"rk/schema/{name}.py"
        for name in (
            "fidelity",
            "channels",
            "execution",
            "workloads",
            "agentic",
            "hashing",
            "traces",
            "versions",
        )
    ),
)
REQUIRED_COMPONENTS = ("asic_placeholder.yaml", "nvidia_h100_sxm.yaml")
# Javid approved the common KV matrix plus H100-only compute formats (U0002).
PRECISIONS = ({"compute": "fp16", "kv_cache": "fp16"}, {"compute": "fp16", "kv_cache": "fp8"})
H100_PRECISIONS = ({"compute": "bf16", "kv_cache": "bf16"}, {"compute": "fp8", "kv_cache": "fp8"})


def component_precisions(name: str) -> tuple[dict[str, str], ...]:
    """Historical retained inventory only; never infer precision for a new component."""
    if name == "asic_placeholder.yaml":
        return PRECISIONS
    if name == "nvidia_h100_sxm.yaml":
        return PRECISIONS + H100_PRECISIONS
    raise ValueError("Explicit ComponentPrecision required for new component: " + name)


QUERIES = [
    {"phase": "decode", "batch": b, "total_context_tokens": b * t}
    for b in (1, 8, 32)
    for t in (128, 512, 4096, 16384)
] + [
    {
        "phase": "prefill",
        "total_prompt_tokens": n * length,
        "sum_of_squared_prompt_tokens": n * length * length,
        "n_prompts": n,
        "prompt_tokens": length,
    }
    for n in (1, 4, 16)
    for length in (128, 512, 2048, 4096)
]

# Executed ONLY in rk-sim's interpreter, via stdin. Imports never enter this process.
ORACLE_PROGRAM = r"""
import json
import sys
import hashlib
import inspect
from pathlib import Path
from rk.components.loader import load_component_file
from rk.engine.f0.compute import UnsupportedPrecision, iteration_cost
from rk.engine.orchestrator import _Instance, _accelerator
from rk.schema.execution import Precision
from rk.schema.fidelity import FidelityMap
from rk.schema.workloads import ModelSpec

request = json.load(sys.stdin)
rows = []
refusals = []
for component in request['components']:
    descriptor = load_component_file(Path(component['path']))
    instance = _Instance(descriptor.id, 1, descriptor,
        FidelityMap(compute='STUB', memory='STUB', network='STUB', runtime='STUB'), None)
    if component.get('direct_refusals'):
        baseline = Precision.model_validate(component['precisions'][0])
        accelerator, _, _ = _accelerator(instance, baseline)
        source_file = inspect.getsourcefile(type(accelerator).peak_op_per_s)
        source_sha = hashlib.sha256(Path(source_file).read_bytes()).hexdigest()
        if source_sha != request['direct_peak_source_sha256']:
            raise AssertionError('direct peak callable source drift')
        for precision_data in component['direct_refusals']:
            unsupported = Precision.model_validate(precision_data)
            event = {'component_params_file': 'components/' + component['name'],
                'component_params_sha256': component['sha256'], 'rk_sha': request['sha'],
                'compute': unsupported.compute.value, 'kv_cache': unsupported.kv_cache.value,
                'boundary': 'Accelerator.peak_op_per_s', 'callable_source_sha256': source_sha}
            try:
                accelerator.peak_op_per_s(unsupported.compute)
            except UnsupportedPrecision as exc:
                event.update(execution='refused', exception=type(exc).__name__, message=str(exc))
            except Exception as exc:
                event.update(execution='execution_failed', exception=type(exc).__name__,
                             message=str(exc) or type(exc).__name__)
            else:
                event.update(execution='succeeded', exception=None,
                             message='Direct peak returned without refusing')
            refusals.append(event)
    elif component['name'] == 'asic_placeholder.yaml':
        # Historical retained-only mode: these are iteration-level observations,
        # never relabelled direct-peak evidence for the expanded U2 inventory.
        baseline = Precision(compute='fp16', kv_cache='fp16')
        accelerator, _, _ = _accelerator(instance, baseline)
        for compute in ('bf16', 'fp8'):
            unsupported = Precision(compute=compute, kv_cache=compute)
            try:
                iteration_cost(ModelSpec.model_validate(request['models'][0]['model']),
                               accelerator, unsupported)
            except UnsupportedPrecision as exc:
                refusals.append({'component_params_file': 'components/' + component['name'],
                    'compute': compute, 'kv_cache': compute,
                    'exception': type(exc).__name__, 'message': str(exc)})
            else:
                raise AssertionError('placeholder unexpectedly supports ' + compute)
    for sidecar in request['models']:
        model = ModelSpec.model_validate(sidecar['model'])
        for precision_data in component['precisions']:
            precision = Precision.model_validate(precision_data)
            accelerator, contributors, badge = _accelerator(instance, precision)
            for tp in (1, 8):
                cost = iteration_cost(model, accelerator, precision, tp=tp)
                for index, query in enumerate(request['queries']):
                    if query['phase'] == 'decode':
                        args = (query['batch'], query['total_context_tokens'])
                        counts = cost.decode_counts(*args)
                        duration = cost.decode_s(*args)
                    else:
                        args = (query['total_prompt_tokens'], query['sum_of_squared_prompt_tokens'])
                        counts = cost.prefill_counts(*args)
                        duration = cost.prefill_s(*args)
                    rows.append({
                        'id': '/'.join((sidecar['id'], precision.compute.value,
                            precision.kv_cache.value, 'tp' + str(tp),
                            component['name'], str(index))),
                        'rk_sha': request['sha'], 'model_id': sidecar['id'],
                        'model': model.model_dump(mode='json'), 'model_shape': sidecar['shape'],
                        'model_sources': sidecar['sources'],
                        'precision': precision.model_dump(mode='json'), 'tp': tp, 'query': query,
                        'component_params_file': 'components/' + component['name'],
                        'component_params_sha256': component['sha256'],
                        'counts_scope': 'replica', 'duration_scope': 'one_tp_rank_no_collectives',
                        'counts': {name: getattr(counts, name) for name in
                            ('matrix_ops', 'memory_read_bytes', 'memory_write_bytes')},
                        'duration_s': duration,
                        'duration_method': query['phase'] + '_s',
                        'contributors': list(contributors), 'badge': badge.value,
                        'omissions': ['inter-chip collectives', 'activation memory traffic',
                                      'decode KV writes' if query['phase'] == 'decode'
                                      else 'non-KV writes'],
                    })
print(json.dumps({'rows': rows, 'refusals': refusals}, sort_keys=True, allow_nan=False))
"""


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def check_clone(root: Path, sha: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", sha) or sha != PIN:
        raise ValueError(f"U1 requires the full pinned SHA {PIN}, got {sha}")
    actual = git(root, "rev-parse", "HEAD")
    if actual != sha:
        raise ValueError(f"rk-sim HEAD {actual} differs from requested {sha}")
    if git(root, "status", "--porcelain", "--untracked-files=all", "--ignore-submodules=none"):
        raise ValueError("rk-sim must have a clean tree (including untracked files)")
    flagged = [
        entry
        for entry in git(root, "ls-files", "-v", "-z").split("\0")
        if entry and not entry.startswith("H ")
    ]
    if flagged:
        raise ValueError(f"rk-sim index flags hide source changes: {flagged}")
    # Use an external oracle environment. Ignored files may shadow tracked modules;
    # even caches are unnecessary because the bridge uses a fresh pycache prefix.
    ignored = git(root, "ls-files", "--others", "--ignored", "--exclude-standard", "-z")
    if ignored:
        raise ValueError(
            "rk-sim has ignored files; use a pristine checkout and external environment"
        )


def check_adr_pin(adr: Path, sha: str, *, pre_contract: bool = False) -> None:
    if not adr.exists():
        if pre_contract:
            return
        raise ValueError(
            "U0001 missing: strict integration requires its dedicated upstream reference"
        )
    # U0001 identifies the upstream in its dedicated Markdown reference line.
    # Repository baseline/history hashes elsewhere in the ADR are not upstream pins.
    references = re.findall(
        r"^\*\*Reference:\*\*[ \t]+rk-sim\b([^\n]*)$", adr.read_text(), re.MULTILINE
    )
    if len(references) != 1:
        raise ValueError(
            "U0001 requires one explicit upstream reference: "
            "**Reference:** rk-sim `<full SHA>`; "
            f"found {len(references)} reference lines"
        )
    reference = references[0]
    pinned = re.fullmatch(r"[ \t]+`([0-9a-f]{40})`(?:[ \t]*,.*|[ \t]*)", reference)
    if pinned is None or len(re.findall(r"\b[0-9a-f]{40}\b", reference)) != 1:
        raise ValueError(
            "U0001 upstream reference must identify one unambiguous full SHA "
            "immediately after **Reference:** rk-sim"
        )
    if pinned.group(1) != sha:
        raise ValueError(f"U0001 upstream rk-sim pin {pinned.group(1)} differs from required {sha}")


def check_contract_pin(root: Path, *, pre_contract: bool = False) -> None:
    check_adr_pin(
        root / "docs/decisions/U0001-the-integration-contract.md", PIN, pre_contract=pre_contract
    )
    common = root / "contract/uarch_contract/common.py"
    if not common.exists():
        if pre_contract:
            return
        raise ValueError("RK_SCHEMA_SNAPSHOT missing: Lane A contract is required")
    values = [
        node.value
        for node in ast.parse(common.read_text()).body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "RK_SCHEMA_SNAPSHOT" for t in node.targets)
    ]
    if not values and pre_contract:
        return
    if len(values) != 1 or not isinstance(values[0], ast.Constant) or values[0].value != PIN:
        raise ValueError(f"RK_SCHEMA_SNAPSHOT must equal upstream pin {PIN}")


def safe_path(name: str) -> bool:
    path = Path(name)
    return bool(name) and not path.is_absolute() and ".." not in path.parts and str(path) == name


def snapshot_bytes(files: dict[str, bytes], sha: str) -> dict[str, bytes]:
    if "MANIFEST.json" in files or any(not safe_path(name) for name in files):
        raise ValueError("unsafe or reserved snapshot path")
    manifest = {
        "rk_sha": sha,
        "files": {name: digest(data) for name, data in sorted(files.items())},
    }
    return {**files, "MANIFEST.json": canonical(manifest)}


def check_manifest(root: Path, sha: str = PIN) -> None:
    for path in (root, *root.parents):
        if path.is_symlink():
            raise ValueError(f"MANIFEST: symlink root or ancestor {path}")
    if not (root / "MANIFEST.json").is_file():
        raise ValueError(f"missing {root}/MANIFEST.json; human vendor operation required")
    manifest = json.loads((root / "MANIFEST.json").read_text())
    if manifest["rk_sha"] != sha:
        raise ValueError(f"MANIFEST.json: rk_sha must be {sha}")
    for name, expected in manifest["files"].items():
        if not safe_path(name) or name == "MANIFEST.json":
            raise ValueError(f"MANIFEST.json: unsafe path {name}")
        path = root / name
        if path.is_symlink() or not path.is_file() or digest(path.read_bytes()) != expected:
            raise ValueError(f"MANIFEST mismatch: {name}")
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"MANIFEST: symlink {path.relative_to(root)}")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    expected_files = set(manifest["files"]) | {"MANIFEST.json"}
    if actual != expected_files:
        raise ValueError(f"MANIFEST file set differs: {sorted(actual ^ expected_files)}")


def publish_snapshot(destination: Path, files: dict[str, bytes]) -> str:
    """Stage atomically. Existing output must be identical; never overwrite reviewed data."""
    if destination.exists():
        check_manifest(destination)
        actual = {
            p.relative_to(destination).as_posix(): p.read_bytes()
            for p in destination.rglob("*")
            if p.is_file()
        }
        if actual != files:
            raise ValueError(f"{destination}: different output; review before replacing snapshot")
        return "verified-identical"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".vendor-", dir=destination.parent) as temporary:
        stage = Path(temporary) / "snapshot"
        stage.mkdir()
        for name, data in sorted(files.items()):
            if not safe_path(name):
                raise ValueError(f"unsafe path {name}")
            path = stage / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(0o444)
        check_manifest(stage)
        stage.rename(destination)
    return "created"


def oracle_command(rk: Path, program: str | None = None) -> list[str]:
    # --no-sync/--frozen prohibit dependency or lockfile writes into the read-only checkout.
    # The human must provision rk-sim's environment first. -B prevents source pycache writes.
    return [
        "uv",
        "run",
        "--project",
        str(rk),
        "--frozen",
        "--no-sync",
        "python",
        "-I",
        "-B",
        "-c",
        ORACLE_PROGRAM if program is None else program,
    ]


def oracle_environment(rk: Path) -> dict[str, str]:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONPATH", None)
    env.pop("VIRTUAL_ENV", None)
    environment = Path(env.get("UV_PROJECT_ENVIRONMENT", str(rk / ".venv")))
    if not environment.is_absolute():
        environment = rk / environment
    if not (environment / "bin/python").is_file():
        raise ValueError(
            "provision rk-sim's locked environment before the human vendor command; "
            "see U1-U-P2-handoff.md (no environment is created by this tool)"
        )
    if environment.resolve().is_relative_to(rk.resolve()):
        raise ValueError(
            "provision an external oracle environment outside the pristine rk-sim tree"
        )
    env["UV_PROJECT_ENVIRONMENT"] = str(environment.resolve())
    return env


ENVIRONMENT_PROGRAM = """
import importlib.metadata, json, platform, re
packages = {}
for dist in importlib.metadata.distributions():
    name = re.sub(r"[-_.]+", "-", dist.metadata["Name"]).lower()
    if name in packages:
        raise ValueError("duplicate installed distribution: " + name)
    packages[name] = dist.version
print(json.dumps({"python_version": platform.python_version(),
                 "implementation": platform.python_implementation(), "packages": packages},
                 sort_keys=True))
"""


def run_oracle(
    rk: Path, env: dict[str, str], program: str, request: str | None = None
) -> subprocess.CompletedProcess[str]:
    # A fresh prefix prevents reading pre-existing pyc files; -B prevents writing any.
    with tempfile.TemporaryDirectory(prefix="uarch-oracle-pycache-") as cache:
        command = oracle_command(rk, program)
        command[-2:-2] = ["-X", "pycache_prefix=" + cache]
        return subprocess.run(
            command, cwd=rk, env=env, input=request, text=True, capture_output=True, check=True
        )


def verify_oracle_environment(rk: Path, env: dict[str, str]) -> None:
    try:
        subprocess.run(
            [
                "uv",
                "sync",
                "--project",
                str(rk),
                "--locked",
                "--check",
                "--offline",
                "--no-default-groups",
            ],
            cwd=rk,
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise ValueError(
            "oracle environment is not synchronized with its locked base selection: "
            + str(exc.stderr)
        ) from exc


def record_oracle_environment(rk: Path, env: dict[str, str]) -> dict[str, Any]:
    result = run_oracle(rk, env, ENVIRONMENT_PROGRAM)
    metadata: dict[str, Any] = json.loads(result.stdout)
    metadata["uv_lock_sha256"] = digest((rk / "uv.lock").read_bytes())
    validate_environment_metadata(metadata, (rk / "uv.lock").read_bytes())
    return metadata


def validate_environment_metadata(metadata: dict[str, Any], lock: bytes) -> None:
    if set(metadata) != {"python_version", "implementation", "packages", "uv_lock_sha256"}:
        raise ValueError("GENERATOR environment metadata has missing or unknown fields")
    if metadata["uv_lock_sha256"] != digest(lock):
        raise ValueError("GENERATOR environment lock digest mismatch")
    if (
        not isinstance(metadata["python_version"], str)
        or not re.fullmatch(r"3\.\d+\.\d+", metadata["python_version"])
        or int(metadata["python_version"].split(".")[1]) < 12
    ):
        raise ValueError("GENERATOR environment requires a recorded Python >= 3.12 version")
    if metadata["implementation"] != "CPython":
        raise ValueError("GENERATOR environment requires the reviewed CPython runtime")
    locked = {(p["name"], p["version"]) for p in tomllib.loads(lock.decode())["package"]}
    packages = metadata["packages"]
    if not isinstance(packages, dict) or not {"pydantic", "pydantic-core"} <= packages.keys():
        raise ValueError("GENERATOR environment must record installed oracle packages")
    if any((name, version) not in locked for name, version in packages.items()):
        raise ValueError("GENERATOR environment package versions differ from the recorded lock")
    # This validates the recorded inventory, not CI's independently locked test environment.


def check_generator(root: Path, *, current: bool = True) -> dict[str, Any]:
    """Recorded identity is distinct from manifest integrity and current compatibility."""
    metadata: dict[str, Any] = json.loads((root / "GENERATOR.json").read_text())
    base = {"rk_sha", "counts_scope", "duration_scope", "script_sha256", "oracle_program_sha256"}
    if set(metadata) not in (base, base | {"environment"}):
        raise ValueError("GENERATOR metadata has missing or unknown fields")
    if (
        metadata["rk_sha"] != PIN
        or metadata["counts_scope"] != "replica"
        or metadata["duration_scope"] != "one_tp_rank_no_collectives"
    ):
        raise ValueError("GENERATOR pin/scopes disagree with snapshot contract")
    for field in ("script_sha256", "oracle_program_sha256"):
        if not isinstance(metadata[field], str) or not re.fullmatch(
            r"[0-9a-f]{64}", metadata[field]
        ):
            raise ValueError(f"GENERATOR invalid {field}")
    if "environment" in metadata:
        if digest((root / "uv.lock").read_bytes()) != PINNED_UV_LOCK_SHA256:
            raise ValueError("GENERATOR environment lock differs from pinned upstream lock")
        validate_environment_metadata(metadata["environment"], (root / "uv.lock").read_bytes())
    if current:
        if (root / "u2-inputs").is_dir():
            check_snapshot_inputs(root, check_support=True)
        problems = []
        if metadata["script_sha256"] != digest(Path(__file__).read_bytes()):
            problems.append("generator script fingerprint differs")
        if metadata["oracle_program_sha256"] != digest(ORACLE_PROGRAM.encode()):
            problems.append("oracle program fingerprint differs")
        if "environment" not in metadata:
            problems.append("locked oracle environment metadata missing")
        if problems:
            raise ValueError("GENERATOR current incompatibility: " + "; ".join(problems))
    return metadata


def check_snapshot_inputs(root: Path, *, check_support: bool = False) -> None:
    components = {p.name for p in (root / "components").iterdir() if p.is_file()}
    rows = json.loads((root / "parity/fixtures.json").read_text())
    checked = None
    if (root / "u2-inputs").is_dir():
        from scripts.u2_inputs import load_inputs

        checked = load_inputs(
            root / "u2-inputs",
            digest((root / "u2-inputs/SHA256SUMS").read_bytes()),
            check_support=check_support,
        )
        for directory, expected in (
            (
                "components",
                {
                    role: checked.descriptors[entry.component_id]
                    for entry in checked.entries
                    for role in [
                        Path(entry.binding.component_file).name
                        if entry.binding.kind == "upstream_only"
                        else "npu-l4.yaml"
                    ]
                },
            ),
            (
                "model_shapes",
                {p.name: p.read_bytes() for p in (checked.root / "model_shapes").glob("*.json")},
            ),
        ):
            outer = root / directory
            if any(p.is_symlink() for p in (outer, *outer.rglob("*"))):
                raise ValueError("frozen output copy contains symlink: " + directory)
            actual = {
                p.relative_to(outer).as_posix(): p.read_bytes()
                for p in outer.rglob("*")
                if p.is_file()
            }
            if actual != expected:
                raise ValueError("frozen output copy inventory/bytes differ: " + directory)
    validate_matrix(rows, components, precisions=checked.matrix if checked else None)
    validate_refusals(
        json.loads((root / "parity/refusals.json").read_text()),
        expanded=checked is not None,
        callable_source_sha256=digest((root / "rk/engine/f0/compute.py").read_bytes())
        if checked
        else None,
    )
    sidecars = {p.stem: json.loads(p.read_text()) for p in (root / "model_shapes").glob("*.json")}
    if set(sidecars) != {r["model_id"] for r in rows}:
        raise ValueError("model sidecar inventory differs from matrix")
    for row in rows:
        component = row["component_params_file"]
        if (
            component != "components/" + Path(component).name
            or Path(component).name not in components
        ):
            raise ValueError("invalid component path in matrix")
        if digest((root / component).read_bytes()) != row["component_params_sha256"]:
            raise ValueError("component digest differs from matrix")
        sidecar = sidecars[row["model_id"]]
        if (
            sidecar["id"] != row["model_id"]
            or sidecar["model"] != row["model"]
            or sidecar["shape"] != row["model_shape"]
            or sidecar["sources"] != row["model_sources"]
        ):
            raise ValueError("model sidecar content/attribution differs from matrix")


def collect_snapshot(
    rk: Path,
    sha: str,
    params: list[Path],
    shapes: Path,
    *,
    input_root: Path | None = None,
    input_manifest_sha256: str | None = None,
) -> dict[str, bytes]:
    checked = None
    if input_root is not None:
        from scripts.u2_inputs import load_inputs

        if params or input_manifest_sha256 is None:
            raise ValueError("explicit U2 input manifest required; --params cannot override it")
        checked = load_inputs(input_root, input_manifest_sha256)
    elif input_manifest_sha256 is not None:
        raise ValueError("input manifest without input root")
    check_clone(rk, sha)
    files = {name: (rk / name).read_bytes() for name in SOURCES}
    files["schema.json"] = (rk / "web/src/schema.json").read_bytes()
    files["uv.lock"] = (rk / "uv.lock").read_bytes()
    models = (
        list(checked.models)
        if checked
        else [json.loads(path.read_text()) for path in sorted(shapes.glob("*.json"))]
    )
    if len(models) < 3:
        raise ValueError("at least three sourced ModelShape sidecars required")
    components: list[dict[str, Any]] = []
    paths = (
        [checked.root / "components" / name for name in checked.matrix]
        if checked
        else [rk / "rk/components/library/compute" / name for name in REQUIRED_COMPONENTS] + params
    )
    for path in paths:
        data = path.read_bytes()
        name = path.name
        key = "components/" + name
        if key in files:
            if files[key] != data:
                raise ValueError(f"component filename collision: {name}")
            continue
        files[key] = data
        components.append(
            {
                "name": name,
                "path": str(path.resolve()),
                "sha256": digest(data),
                "precisions": checked.matrix[name] if checked else component_precisions(name),
                "direct_refusals": tuple(
                    {"compute": fmt, "kv_cache": fmt}
                    for fmt in (
                        ()
                        if checked is None
                        else ("bf16", "fp8")
                        if name == "asic_placeholder.yaml"
                        else ("fp16", "fp8")
                        if name == "npu-l4.yaml"
                        else ()
                    )
                ),
            }
        )
    request: dict[str, Any] = {
        "sha": sha,
        "models": models,
        "queries": QUERIES,
        "components": components,
        "direct_peak_source_sha256": digest(files["rk/engine/f0/compute.py"]),
    }
    if checked:
        for path in checked.root.rglob("*"):
            if path.is_file():
                files["u2-inputs/" + path.relative_to(checked.root).as_posix()] = path.read_bytes()
    env = oracle_environment(rk)
    verify_oracle_environment(rk, env)
    environment = record_oracle_environment(rk, env)
    files["GENERATOR.json"] = canonical(
        {
            "script_sha256": digest(Path(__file__).read_bytes()),
            "oracle_program_sha256": digest(ORACLE_PROGRAM.encode()),
            "rk_sha": sha,
            "counts_scope": "replica",
            "duration_scope": "one_tp_rank_no_collectives",
            "environment": environment,
        }
    )
    result = run_oracle(rk, env, ORACLE_PROGRAM, json.dumps(request))
    output = json.loads(result.stdout)
    rows = output["rows"]
    validate_refusals(
        output["refusals"],
        expanded=checked is not None,
        callable_source_sha256=request["direct_peak_source_sha256"] if checked else None,
    )
    files["parity/refusals.json"] = canonical(output["refusals"])
    validate_matrix(
        rows, {item["name"] for item in components}, precisions=checked.matrix if checked else None
    )
    files["parity/fixtures.json"] = canonical(rows)
    for model in models:
        files[f"model_shapes/{model['id']}.json"] = canonical(model)
    verify_oracle_environment(rk, env)
    if record_oracle_environment(rk, env) != environment:
        raise ValueError("oracle environment changed during generation")
    if files["uv.lock"] != (rk / "uv.lock").read_bytes():
        raise ValueError("oracle lock changed during generation")
    # Recheck after execution. Input drift must not produce a partially trusted snapshot.
    check_clone(rk, sha)
    for source in SOURCES:
        if files[source] != (rk / source).read_bytes():
            raise ValueError(f"input changed during generation: {source}")
    if files["schema.json"] != (rk / "web/src/schema.json").read_bytes():
        raise ValueError("input changed during generation: schema.json")
    for component in components:
        if digest(Path(component["path"]).read_bytes()) != component["sha256"]:
            raise ValueError(f"input changed during generation: {component['name']}")
    if checked:
        assert input_root is not None and input_manifest_sha256 is not None
        load_inputs(input_root, input_manifest_sha256)
    return snapshot_bytes(files, sha)


def validate_matrix(
    rows: list[dict[str, Any]],
    components: set[str] | None = None,
    *,
    precisions: dict[str, tuple[dict[str, str], ...]] | None = None,
) -> None:
    import math

    components = components or {Path(row["component_params_file"]).name for row in rows}
    if not set(REQUIRED_COMPONENTS) <= components:
        raise ValueError("missing required component params files")
    if precisions is not None and set(precisions) != components:
        raise ValueError("explicit precision/component inventory differs")
    models = {row["model_id"] for row in rows}
    if len(models) < 3:
        raise ValueError("missing models: require at least three")
    expected = {
        (
            model,
            json.dumps(precision, sort_keys=True),
            tp,
            component,
            json.dumps(query, sort_keys=True),
        )
        for model in models
        for component in components
        for precision in (precisions[component] if precisions else component_precisions(component))
        for tp in (1, 8)
        for query in QUERIES
    }
    seen = set()
    ids = set()
    for row in rows:
        key = (
            row["model_id"],
            json.dumps(row["precision"], sort_keys=True),
            row["tp"],
            Path(row["component_params_file"]).name,
            json.dumps(row["query"], sort_keys=True),
        )
        if key in seen or row["id"] in ids:
            raise ValueError(f"duplicate fixture: {row['id']}")
        seen.add(key)
        ids.add(row["id"])
        if row["rk_sha"] != PIN or row["counts_scope"] != "replica":
            raise ValueError(f"{row['id']}: incorrect pin/counts scope")
        if (
            row["duration_scope"] != "one_tp_rank_no_collectives"
            or row["duration_method"] != row["query"]["phase"] + "_s"
            or not math.isfinite(row["duration_s"])
            or row["duration_s"] <= 0
        ):
            raise ValueError(f"{row['id']}: invalid oracle duration")
        if not re.fullmatch(r"[0-9a-f]{64}", row["component_params_sha256"]):
            raise ValueError(f"{row['id']}: missing component digest")
        if set(row["counts"]) != {"matrix_ops", "memory_read_bytes", "memory_write_bytes"}:
            raise ValueError(f"{row['id']}: incomplete IterationCounts")
        for name, value in row["counts"].items():
            if value is None and name == "memory_write_bytes" and row["query"]["phase"] == "decode":
                continue
            if value is None or not math.isfinite(value) or value < 0:
                raise ValueError(f"{row['id']}: invalid {name}")
        if row["query"]["phase"] == "decode" and row["counts"]["memory_write_bytes"] is not None:
            raise ValueError(f"{row['id']}: pinned oracle leaves decode writes unmodelled")
    if seen != expected:
        raise ValueError(
            f"incomplete matrix: missing={len(expected - seen)}, extra={len(seen - expected)}"
        )


def validate_refusals(
    refusals: list[dict[str, Any]],
    *,
    expanded: bool = False,
    callable_source_sha256: str | None = None,
) -> None:
    expected = {
        ("components/asic_placeholder.yaml", fmt, fmt, "UnsupportedPrecision")
        for fmt in ("bf16", "fp8")
    }
    if expanded:
        expected |= {
            ("components/npu-l4.yaml", fmt, fmt, "UnsupportedPrecision") for fmt in ("fp16", "fp8")
        }
    actual = {
        (r["component_params_file"], r["compute"], r["kv_cache"], r["exception"]) for r in refusals
    }
    if (
        actual != expected
        or len(refusals) != len(expected)
        or any(not r["message"] for r in refusals)
    ):
        raise ValueError("missing actual UnsupportedPrecision refusals")
    if callable_source_sha256 is not None or expanded:
        if callable_source_sha256 is None or any(
            r.get("boundary") != "Accelerator.peak_op_per_s"
            or r.get("callable_source_sha256") != callable_source_sha256
            for r in refusals
        ):
            raise ValueError("direct peak boundary/source mismatch")


def retained_provenance_root() -> Path:
    """Committed immutable U0002 source subset; independent of the adoption destination."""
    return ROOT / "contract/provenance" / ("rk-sim@" + PIN) / HISTORICAL_MANIFEST_SHA256


def retained_provenance(directory: Path | None = None) -> dict[str, bytes]:
    """Authenticate original manifest bytes AND every retained descriptor/sidecar entry.

    This is a source subset, not a replacement oracle snapshot. Unneeded oracle/source
    members named by the original manifest are not claimed present or re-generated.
    """
    root = retained_provenance_root() if directory is None else directory
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError("historical provenance symlink ancestor")
    try:
        raw = (root / "MANIFEST.json").read_bytes()
    except OSError as exc:
        raise ValueError("historical provenance manifest missing") from exc
    if digest(raw) != HISTORICAL_MANIFEST_SHA256:
        raise ValueError("historical provenance manifest identity differs")
    manifest = json.loads(raw)
    if manifest["rk_sha"] != PIN:
        raise ValueError("historical provenance pin differs")
    names = {
        name for name in manifest["files"] if name.startswith(("components/", "model_shapes/"))
    }
    result = {"MANIFEST.json": raw}
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("historical provenance symlink member")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if actual != names | {"MANIFEST.json"}:
        raise ValueError("historical provenance exact source subset differs")
    for name in sorted(names):
        data = (root / name).read_bytes()
        if digest(data) != manifest["files"][name]:
            raise ValueError("historical provenance entry differs: " + name)
        result[name] = data
    return result


def validate_u2_component_inputs(
    values: list[dict[str, Any]],
    descriptors: dict[str, bytes],
    artifacts: dict[str, Any],
    *,
    require_full: bool = True,
    provenance_root: Path | None = None,
) -> tuple[ComponentPrecision, ...]:
    """Validate explicit shared bindings; this is not real pinned bridge verification.

    Full mode requires the exact accepted seven-pair inventory. Partial mode serves
    received/retained input checks only and cannot authorize generator execution.
    """
    import yaml
    from uarch_contract.exports import ComponentExport, ComponentPrecision, ExecutionModelInput
    from uarch_contract.hashing import (
        content_hash,
        resolve_artifact,
        sha256,
        spec_hash,
        verify_identity,
    )

    entries = tuple(ComponentPrecision.model_validate(v) for v in values)
    ids = [entry.component_id for entry in entries]
    if len(set(ids)) != len(ids) or set(ids) != set(descriptors):
        raise ValueError("ComponentBindingMismatch: unique exact descriptor inventory required")
    roles: set[str] = set()
    historical = (
        retained_provenance(provenance_root)
        if any(e.binding.kind == "upstream_only" for e in entries)
        else {}
    )
    for entry in entries:
        verify_identity(entry, "precision_hash")
        binding = entry.binding
        verify_identity(binding, "binding_hash")
        if binding.upstream_sha != PIN:
            raise ValueError("ComponentBindingMismatch: upstream pin")
        raw = descriptors[entry.component_id]
        descriptor = yaml.safe_load(raw)
        if descriptor["id"] != entry.component_id:
            raise ValueError("ComponentBindingMismatch: descriptor id")
        execution = ExecutionModelInput.model_validate(
            resolve_artifact(binding.execution_model_hash, artifacts)
        )
        if execution.kind != "scalar_efficiency" or execution.acceptance != "accepted_input":
            raise ValueError("ExecutionModelMismatch: accepted scalar input required")
        if descriptor["execution_model"]["kind"] != execution.kind:
            raise ValueError("ExecutionModelMismatch: descriptor kind")
        original_efficiency = descriptor["execution_model"]["value"]
        if any(
            original_efficiency[k] != getattr(execution.compute, k)
            for k in ("value", "unit", "provenance", "source", "date")
        ):
            raise ValueError("ExecutionModelMismatch: descriptor efficiency")
        pairs = {(p.compute.value, p.kv_cache.value) for p in entry.precisions}
        if any(p.kv_cache not in binding.supported_kv_storage for p in entry.precisions):
            raise ValueError("UnsupportedPrecision: undeclared KV storage")
        if binding.kind == "upstream_only":
            if sha256(raw) != binding.component_bytes_sha256:
                raise ValueError("ComponentBindingMismatch: upstream descriptor bytes")
            if not safe_path(binding.component_file) or binding.component_file not in (
                "components/asic_placeholder.yaml",
                "components/nvidia_h100_sxm.yaml",
            ):
                raise ValueError("ComponentBindingMismatch: unapproved upstream component")
            if (
                sha256(historical["MANIFEST.json"]) != binding.oracle_manifest_sha256
                or raw != historical[binding.component_file]
            ):
                raise ValueError("ComponentBindingMismatch: retained bytes/manifest changed")
            role = Path(binding.component_file).name
            approved = {(p["compute"], p["kv_cache"]) for p in component_precisions(role)}
            if execution.compute.value != 0.55 or execution.compute.provenance != "stub":
                raise ValueError("ExecutionModelMismatch: retain .55 stub input")
        else:
            role = "npu-l4.yaml"
            approved = {("bf16", "bf16")}
            truth = ComponentExport.model_validate(
                resolve_artifact(binding.primary_export_hash, artifacts)
            )
            if (
                truth.hardware_spec_hash != binding.hardware_spec_hash
                or truth.component_id != entry.component_id
                or truth.derivation_hash != binding.derivation_hash
                or truth.execution_model_hash != binding.execution_model_hash
                or truth.design_status != binding.design_status
            ):
                raise ValueError("ComponentBindingMismatch: export truth")
            from uarch_contract.derivation import Derivation
            from uarch_contract.hardware import HardwareSpec

            from rkuarch.hw.export import project_for_oracle

            derivation = Derivation.model_validate(
                resolve_artifact(binding.derivation_hash, artifacts)
            )
            spec = yaml.safe_load((ROOT / "hw/designs/npu-l4.yaml").read_text())
            if binding.hardware_spec_hash != spec_hash(spec):
                raise ValueError("ComponentBindingMismatch: accepted H1 required")
            if binding.projected_descriptor_bytes_sha256 != sha256(
                raw
            ) or binding.projected_descriptor_content_hash != content_hash(descriptor):
                raise ValueError("ComponentBindingMismatch: projection bytes/content")
            compute = execution.compute
            if (
                compute.value != 1.0
                or compute.kind != "claim"
                or compute.provenance != "stub"
                or any(v is not None for v in (compute.source, compute.date, compute.rationale))
                or execution.evidence_hashes
                or "unvalidated" not in execution.assumption_note.lower()
            ):
                raise ValueError("ExecutionModelMismatch: nominal1.0 claim/stub unvalidated input")
            # Replay A's pure local source/projection checks; no pinned bridge or oracle call.
            expected_bytes, expected_binding = project_for_oracle(
                HardwareSpec.model_validate(spec), truth, derivation, execution, upstream_sha=PIN
            )
            if raw != expected_bytes or binding != expected_binding:
                raise ValueError("ComponentBindingMismatch: source projection/losses")
        if role in roles or pairs != approved:
            raise ValueError("ComponentBindingMismatch: exact seven approved pairs required")
        roles.add(role)
    if require_full and roles != {"asic_placeholder.yaml", "nvidia_h100_sxm.yaml", "npu-l4.yaml"}:
        raise ValueError("ComponentBindingMismatch: actual npu-l4 export still required")
    return entries


def staging_destination(output_root: Path, adopted_root: Path) -> Path:
    """A distinct review-only output root, never the adopted vendor tree or its parent."""
    for path in (output_root, *output_root.parents):
        if path.is_symlink():
            raise ValueError("staging output must not use symlink ancestors")
    destination, adopted = output_root.resolve(), adopted_root.resolve()
    if destination == adopted or destination in adopted.parents or adopted in destination.parents:
        raise ValueError("staging output overlaps adopted vendor artifacts")
    return destination


def compare_staged_revisions(first: Path, second: Path) -> tuple[str, ...]:
    """Compare complete relative file sets and bytes, including manifests and metadata."""
    if first.resolve() == second.resolve():
        raise ValueError("two distinct preserved generation roots are required")
    check_manifest(first)
    check_manifest(second)

    def files(root: Path) -> dict[str, bytes]:
        return {
            p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()
        }

    left, right = files(first), files(second)
    return tuple(sorted(p for p in left.keys() | right.keys() if left.get(p) != right.get(p)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sha", default=os.environ.get("SHA", PIN))
    parser.add_argument("--rk", type=Path, default=os.environ.get("RK"))
    parser.add_argument("--params", action="append", type=Path, default=[])
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--inputs", type=Path, help="Reviewed explicit U2 input directory")
    parser.add_argument("--input-manifest-sha256", help="Exact reviewed SHA256SUMS digest")
    parser.add_argument(
        "--output-root", type=Path, help="Separate review candidate root; never adopted tree"
    )
    parser.add_argument(
        "--pre-contract",
        action="store_true",
        help="Explicit preparation only: permit absent U0001/contract",
    )
    parser.add_argument(
        "--historical",
        action="store_true",
        help="With --check: integrity/recorded identity only, NOT current compatibility",
    )
    args = parser.parse_args()
    adopted = ROOT / "contract/vendor" / f"rk-sim@{args.sha}"
    destination = adopted
    try:
        if args.output_root is not None:
            destination = staging_destination(args.output_root, adopted)
        if args.inputs is not None and args.output_root is not None:
            staging_destination(args.output_root, args.inputs)
        if args.inputs is not None and args.output_root is None:
            raise ValueError("expanded U2 generation requires a separate --output-root")
        if args.sha != PIN:
            raise ValueError(f"U1 requires {PIN}")
        if args.historical and not args.check:
            raise ValueError("--historical requires --check")
        if not args.historical:
            check_contract_pin(ROOT, pre_contract=args.pre_contract)
        if args.check:
            check_manifest(destination, args.sha)
            check_snapshot_inputs(destination)
            check_generator(destination, current=not args.historical)
            label = (
                "historical integrity and recorded identity ONLY; current compatibility not checked"
                if args.historical
                else "snapshot manifest, matrix and current compatibility verified"
            )
            print(f"{label}: {destination}")
            return
        if os.environ.get("UARCH_HUMAN") != "1":
            raise ValueError("human-only vendor operation: Javid must run with UARCH_HUMAN=1")
        if not args.rk:
            raise ValueError("RK=<path-to-clean-pinned-rk-sim> is required")
        params = args.params + [Path(p) for p in shlex.split(os.environ.get("PARAMS", ""))]
        files = collect_snapshot(
            args.rk.resolve(),
            args.sha,
            params,
            ROOT / "contract/fixtures/model_shapes",
            input_root=args.inputs,
            input_manifest_sha256=args.input_manifest_sha256,
        )
        status = publish_snapshot(destination, files)
        print(f"{status}: {len(files)} files at {destination}")
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"vendor-rk: {exc}\n")


if __name__ == "__main__":
    main()
