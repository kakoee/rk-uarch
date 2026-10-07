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
from typing import Any

PIN = "1e5706e0ebfcc67c1a7333079a35b75f693e9963"
# Independently read at the pinned revision; CI needs no upstream checkout.
PINNED_UV_LOCK_SHA256 = "d984e55723326751ac3f888712f98462a525315ad4693691dbc3f2f5dc7f577c"
ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    "rk/provenance.py",
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
    return PRECISIONS + (H100_PRECISIONS if name == "nvidia_h100_sxm.yaml" else ())


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
    if component['name'] == 'asic_placeholder.yaml':
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


def check_snapshot_inputs(root: Path) -> None:
    components = {p.name for p in (root / "components").iterdir() if p.is_file()}
    rows = json.loads((root / "parity/fixtures.json").read_text())
    validate_matrix(rows, components)
    validate_refusals(json.loads((root / "parity/refusals.json").read_text()))
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


def collect_snapshot(rk: Path, sha: str, params: list[Path], shapes: Path) -> dict[str, bytes]:
    check_clone(rk, sha)
    files = {name: (rk / name).read_bytes() for name in SOURCES}
    files["schema.json"] = (rk / "web/src/schema.json").read_bytes()
    files["uv.lock"] = (rk / "uv.lock").read_bytes()
    models = [json.loads(path.read_text()) for path in sorted(shapes.glob("*.json"))]
    if len(models) < 3:
        raise ValueError("at least three sourced ModelShape sidecars required")
    components: list[dict[str, Any]] = []
    paths = [rk / "rk/components/library/compute" / name for name in REQUIRED_COMPONENTS] + params
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
                "precisions": component_precisions(name),
            }
        )
    request = {"sha": sha, "models": models, "queries": QUERIES, "components": components}
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
    validate_refusals(output["refusals"])
    files["parity/refusals.json"] = canonical(output["refusals"])
    validate_matrix(rows, {item["name"] for item in components})
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
    return snapshot_bytes(files, sha)


def validate_matrix(rows: list[dict[str, Any]], components: set[str] | None = None) -> None:
    import math

    components = components or {Path(row["component_params_file"]).name for row in rows}
    if not set(REQUIRED_COMPONENTS) <= components:
        raise ValueError("missing required component params files")
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
        for precision in component_precisions(component)
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


def validate_refusals(refusals: list[dict[str, Any]]) -> None:
    expected = {
        ("components/asic_placeholder.yaml", fmt, fmt, "UnsupportedPrecision")
        for fmt in ("bf16", "fp8")
    }
    actual = {
        (r["component_params_file"], r["compute"], r["kv_cache"], r["exception"]) for r in refusals
    }
    if actual != expected or len(refusals) != 2 or any(not r["message"] for r in refusals):
        raise ValueError("missing actual placeholder UnsupportedPrecision refusals")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sha", default=os.environ.get("SHA", PIN))
    parser.add_argument("--rk", type=Path, default=os.environ.get("RK"))
    parser.add_argument("--params", action="append", type=Path, default=[])
    parser.add_argument("--check", action="store_true")
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
    destination = ROOT / "contract/vendor" / f"rk-sim@{args.sha}"
    try:
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
            args.rk.resolve(), args.sha, params, ROOT / "contract/fixtures/model_shapes"
        )
        status = publish_snapshot(destination, files)
        print(f"{status}: {len(files)} files at {destination}")
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"vendor-rk: {exc}\n")


if __name__ == "__main__":
    main()
