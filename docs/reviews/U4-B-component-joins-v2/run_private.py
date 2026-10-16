"""Run author-only candidate checks in a fresh tracked export; never install semantics.

Requires the already installed Python tools. No native executable, network, dependency
installation, authority creation or campaign access. Guard mutations are private and restored.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEST = ROOT / "docs/reviews/U4-B-component-joins-v2"
A = "docs/reviews/U4-A-component-release-v1"
PYTHON = "/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python"
BIN = str(Path(PYTHON).parent)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    out = Path(tempfile.mkdtemp(prefix="u4-b-final-joins-"))
    archive = subprocess.check_output(["git", "archive", "HEAD"], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as handle:
        handle.extractall(out, filter="data")
    proposal = json.loads((ROOT / A / "postimages.json").read_text())
    assert sha((ROOT / A / "combined.patch").read_bytes()) == proposal["patch_sha256"]
    for row in proposal["files"]:
        assert sha((out / row["path"]).read_bytes()) == row["base_sha256"]
    subprocess.run(["git", "apply", str(ROOT / A / "combined.patch")], cwd=out, check=True)
    for row in proposal["files"]:
        assert sha((out / row["path"]).read_bytes()) == row["postimage_sha256"]
    for source, target in [
        ("test_candidate.py.txt", "_a_component_candidate.py"),
        ("test_result.py.txt", "_a_component_result.py"),
    ]:
        shutil.copyfile(out / A / source, out / "tests" / target)
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "MYPYPATH")}
    logs = DEST / "checks"
    logs.mkdir(exist_ok=True)
    records = []

    def run(name: str, argv: list[str], expected: int = 0) -> None:
        result = subprocess.run(argv, cwd=out, env=env, text=True, capture_output=True)
        data = (result.stdout + result.stderr).encode()
        (logs / (name + ".log")).write_bytes(data)
        records.append(
            dict(
                name=name,
                argv=argv,
                exit_code=result.returncode,
                expected_exit_code=expected,
                log="checks/" + name + ".log",
                log_sha256=sha(data),
            )
        )
        print(name, result.returncode, flush=True)
        if result.returncode != expected:
            print(result.stdout[-5000:] + result.stderr[-3000:], flush=True)
            raise RuntimeError(name)

    try:
        run(
            "combined",
            [
                PYTHON,
                "-m",
                "pytest",
                "-q",
                "-m",
                "not native",
                "validation/component",
                "tests/unit/test_u4_a_component_mapper.py",
                "tests/unit/test_u4_a_mapped_loader.py",
                "tests/_a_component_candidate.py",
                "tests/_a_component_result.py",
                "docs/reviews/U4-B-component-joins-v2/test_accumulator.py",
                "docs/reviews/U4-B-component-joins-v2/test_carrier.py",
            ],
        )
        mutations = [
            (
                "accumulator-writer",
                "contract/uarch_contract/mapped.py",
                "isinstance(producer, Compute) and producer.accumulator_buffer_id == buf.id",
                "True",
                "docs/reviews/U4-B-component-joins-v2/test_accumulator.py::test_semantic_attack_and_restored_control[other_writer-InvalidDependency]",
            ),
            (
                "live-alias",
                "contract/uarch_contract/mapped.py",
                "ends_before(a, z) or ends_before(z, a)",
                "True",
                "docs/reviews/U4-B-component-joins-v2/test_accumulator.py::test_semantic_attack_and_restored_control[no_order-LiveBufferAlias]",
            ),
            (
                "null-domain",
                "contract/uarch_contract/mapped.py",
                "q.item_id in declared and q.clock_domain is None and q.activity_id is None",
                "q.item_id in declared and q.activity_id is None",
                "docs/reviews/U4-B-component-joins-v2/test_carrier.py::test_queue_bindings_and_restoration[clock-channel_service:6]",
            ),
            (
                "ordinary-owner",
                "contract/uarch_contract/mapped.py",
                "and q.owner_id == a.owner_id",
                "and True",
                "docs/reviews/U4-B-component-joins-v2/test_carrier.py::test_queue_bindings_and_restoration[owner-ordinary]",
            ),
            (
                "rational-mechanism",
                "validation/component/phase_laws.py",
                "start >= 0 and end - start == transaction * 10**12 / bandwidth",
                "True",
                "docs/reviews/U4-B-component-joins-v2/test_carrier.py::test_independent_mechanism_discrimination[channel_duration]",
            ),
        ]
        restoration = []
        for name, path, before, after, selection in mutations:
            target = out / path
            original = target.read_bytes()
            body = original.decode()
            assert body.count(before) == 1, (name, body.count(before))
            try:
                target.write_text(body.replace(before, after))
                # Source-loader timestamp caches cannot hide the injected change.
                for cache in target.parent.glob("__pycache__/*" + target.stem + "*.pyc"):
                    cache.unlink()
                run(name + "-removed", [PYTHON, "-m", "pytest", "-q", selection], 1)
            finally:
                target.write_bytes(original)
                for cache in target.parent.glob("__pycache__/*" + target.stem + "*.pyc"):
                    cache.unlink()
                assert target.read_bytes() == original
            run(name + "-restored", [PYTHON, "-m", "pytest", "-q", selection])
            restoration.append(
                dict(
                    guard=name, path=path, restored_sha256=sha(original), exact_bytes_restored=True
                )
            )
        run(
            "lint",
            [
                BIN + "/ruff",
                "check",
                "validation/component",
                "docs/reviews/U4-B-component-joins-v2",
                "src/rkuarch/mapping/component.py",
                "src/rkuarch/workload/component.py",
                "contract/uarch_contract/mapped.py",
            ],
        )
        run(
            "types",
            [
                BIN + "/mypy",
                "validation/component/observations_v2.py",
                "validation/component/phase_laws.py",
                "validation/component/join_inputs.py",
                "validation/component/observations.py",
                "src/rkuarch/mapping/component.py",
                "src/rkuarch/workload/component.py",
                "contract/uarch_contract/mapped.py",
            ],
        )
        run(
            "schema",
            [
                PYTHON,
                "-c",
                "import sys,runpy;sys.path[:0]=['src','contract','.'];"
                "sys.argv=['generate','--check'];"
                "runpy.run_module('uarch_contract.generate',run_name='__main__')",
            ],
        )
        run("currentness", [PYTHON, "scripts/vendor_rk.py", "--check"])
        command = [
            PYTHON,
            "-c",
            "import sys,json;sys.path[:0]=['src','contract','.'];"
            "from scripts.u2_support import inventory;print(json.dumps(inventory(),sort_keys=True))",
        ]
        before = json.loads(subprocess.check_output(command, cwd=ROOT, env=env))
        after = json.loads(subprocess.check_output(command, cwd=out, env=env))
        delta = {
            p: dict(before=before.get(p), after=after.get(p))
            for p in before.keys() | after.keys()
            if before.get(p) != after.get(p)
        }
        support = dict(
            selected_files=len(after),
            actual_deltas=delta,
            human_generation_required=bool(delta),
            before_inventory_sha256=sha(json.dumps(before, sort_keys=True).encode()),
            after_inventory_sha256=sha(json.dumps(after, sort_keys=True).encode()),
            protected_installation_authorized=False,
        )
        (DEST / "support-audit.json").write_text(
            json.dumps(support, indent=2, sort_keys=True) + "\n"
        )
        (DEST / "restoration.json").write_text(json.dumps(restoration, indent=2) + "\n")
        for row in proposal["files"]:
            assert sha((out / row["path"]).read_bytes()) == row["postimage_sha256"]
    finally:
        report = dict(
            status="author preparation only; no native invocation",
            source_commit=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            export=str(out),
            python=PYTHON,
            patch_sha256=proposal["patch_sha256"],
            commands=records,
        )
        (DEST / "checks.json").write_text(json.dumps(report, indent=2) + "\n")
        print("private export:", out, flush=True)


if __name__ == "__main__":
    main()
