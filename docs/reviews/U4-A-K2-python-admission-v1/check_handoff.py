"""Read-only integrity checks for the unapplied A handoff; no native execution."""

import hashlib
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path.cwd()
PACKAGE = ROOT / "docs/reviews/U4-A-K2-python-admission-v1"
PRIVATE = Path("/tmp/u4-a-admission.0i3ay8e8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> object:
    return json.loads(path.read_bytes())


def main() -> None:
    bindings = json.loads((PACKAGE / "source-bindings.json").read_bytes())
    patches = {
        "src/rkuarch/engines/native/runner.py": "runner.patch",
        "contract/uarch_contract/hardware.py": "hardware-rule.patch",
        "src/rkuarch/engines/native/host.py": "host-session.patch",
    }
    for path, binding in bindings.items():
        assert digest(ROOT / path) == binding["baseline_sha256"]
        assert digest(PACKAGE / "candidate" / path) == binding["candidate_sha256"]
        assert digest(PACKAGE / patches[path]) == binding["patch_sha256"]
        assert digest(PRIVATE / "variants/startup-v2" / path) == binding["candidate_sha256"]

    all_files = [p for p in PACKAGE.rglob("*") if p.is_file()]
    by_hash: dict[str, list[str]] = {}
    for path in all_files:
        by_hash.setdefault(digest(path), []).append(str(path.relative_to(PACKAGE)))
        if path.suffix == ".json":
            read(path)

    receipts: dict[str, object] = {}
    for directory in sorted((PACKAGE / "receipts").iterdir()):
        copies = {}
        for path in directory.iterdir():
            assert path.is_file()
            assert (
                path.read_bytes()
                == (PRIVATE / "receipts" / directory.name / path.name).read_bytes()
            )
            copies[path.name] = digest(path)
        report_path = directory / "report.json"
        report = json.loads(report_path.read_bytes()) if report_path.exists() else {}
        tests = {}
        for name, value in report.get("test_hashes", {}).items():
            tests[name] = by_hash[value.removeprefix("sha256:")]
        receipts[directory.name] = {"exact_private_copies": copies, "executed_helper_copies": tests}

    links = []
    for name in ("README.md", "peer-interface.md", "identity-and-lifecycle.md"):
        for target in re.findall(r"\]\(([^)]+)\)", (PACKAGE / name).read_text()):
            if "://" in target or target.startswith("#"):
                continue
            if target != "handoff-checks.json":
                assert (PACKAGE / target.split("#")[0]).exists(), (name, target)
            links.append({"from": name, "target": target})

    report = json.loads((PACKAGE / "receipts/final-guard/report.json").read_bytes())
    measurements = report["measurements"]
    assert len(measurements) == 12
    assert len({m["signature"] for m in measurements}) == 1
    assert all(m["transport_replays"] == 12 for m in measurements)
    medians = {}
    for config in ("baseline", "rule-only", "per-call", "per-call+rule", "case", "case+rule"):
        subset = [m for m in measurements if m["configuration"] == config]
        assert sorted(m["round"] for m in subset) == [0, 1]
        medians[config] = statistics.median(m["seconds"] for m in subset)
    startup = json.loads((PACKAGE / "receipts/startup/report.json").read_bytes())
    phases = startup["startup_phases"]
    original = sum(p["seconds"] for p in phases if p["api"] == "baseline-public")
    shared = next(p for p in phases if p["api"] == "shared-session")
    assert abs(sum(shared["phase_seconds"].values()) - shared["seconds"]) < 0.001
    join = json.loads((PACKAGE / "receipts/peer-join/report.json").read_bytes())
    controls = join["peer_missing_profile"]["controls"]
    assert [c["refusal"]["type"] for c in controls] == [
        "KeyError",
        "ValueError",
        "KeyError",
        "ValueError",
    ]
    assert all(c["transport_calls_on_refusal"] == 0 for c in controls)
    assert all(c["restored_python_replays"] == 3 for c in controls)
    for row in join["public_resolver_negatives"]:
        assert row["outcomes"]["baseline"] == row["outcomes"]["candidate"]

    sys.path.insert(0, str(ROOT))
    from scripts.u2_support import support_files

    selected = {str(p.relative_to(ROOT)): "sha256:" + digest(p) for p in support_files(root=ROOT)}
    previous = json.loads(
        (
            ROOT / "docs/reviews/U4-A-K2-construction-v1/selected-support-currentness.json"
        ).read_bytes()
    )["selected_files"]
    assert selected == previous
    assert len(selected) == 56
    result = {
        "scope": "Proposal integrity/arithmetic/links/currentness only; zero native executions",
        "candidate_bindings_exact": True,
        "receipt_copies_and_executed_tests": receipts,
        "local_links": links,
        "processing_median_seconds": medians,
        "processing_runner_sha256": report["source_hashes"]["src/rkuarch/engines/native/runner.py"],
        "final_runner_sha256": bindings["src/rkuarch/engines/native/runner.py"]["candidate_sha256"],
        "baseline_two_mode_startup_seconds": original,
        "shared_two_mode_startup_seconds": shared["seconds"],
        "startup_phase_arithmetic_matches": True,
        "final_missing_profile_discriminators_match": True,
        "selected_support_count": len(selected),
        "selected_support_exactly_current": True,
        "full_campaign_slot_count": 133 * 2 * 3,
        "checker_source_sha256": digest(Path(__file__)),
    }
    (PACKAGE / "handoff-checks.json").write_text(json.dumps(result, indent=2) + "\n")
    assert (PACKAGE / "handoff-checks.json").is_file()
    print("Proposal hashes, receipts, helpers, links, arithmetic and support passed")


if __name__ == "__main__":
    main()
