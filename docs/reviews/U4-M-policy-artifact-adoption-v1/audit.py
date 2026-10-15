"""Read-only candidate audit; saved human output only, never production or adoption."""

import hashlib
import json
import runpy
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE = ROOT / "docs/reviews/U4-M-policy-freeze-generation-v1"
PACKAGE = "ccf19227d06a3c520f2599729b5db31297e436ad"
EXPECTED = "b19016be07307ed987037d8a079f85af0366eab018b1132c2668394acd756bcc"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(ok, reason):
    if not ok:
        raise ValueError(reason)


def main():
    pre = runpy.run_path(str(FREEZE / "preflight.py"))
    preflight = pre["preflight"](PACKAGE, during=True)
    u, _, v = pre["load_source"]()

    def forbidden(*args, **kwargs):
        raise AssertionError("producer/oracle invocation forbidden during candidate audit")

    u.prepare_inputs = forbidden
    v.run_oracle = forbidden
    from tests import u2_refresh

    check(Path(u2_refresh.__file__).resolve().is_relative_to(pre["SOURCE"]), "test origin")
    source = pre["SPEC"]
    output = pre["OUTPUT"]
    candidate, old = output / "candidate", u.ADOPTED
    receipt_dir = output / "receipts"
    receipt = json.loads((receipt_dir / "generation-receipt.json").read_bytes())
    check(
        receipt
        == dict(
            adoption_commit_push=False,
            authorization_commit="f0ec16fac79190e4d2d3e7097556520fc6326e36",
            candidate=str(candidate),
            candidate_manifest_sha256=EXPECTED,
            decision="U4-M-policy-freeze-generation-v1",
            input_manifest_sha256=source["input_manifest_sha256"],
            package_commit=PACKAGE,
            runs=2,
            source_commit=source["source_commit"],
            source_tree=source["source_tree"],
            status="created then verified-identical; NOT adopted",
        ),
        "human generation receipt identity",
    )
    check(digest(candidate / "MANIFEST.json") == EXPECTED, "candidate manifest")
    check(
        digest(old / "MANIFEST.json") == source["current_artifact_manifest_sha256"], "old manifest"
    )
    for i, status in enumerate(("created", "verified-identical"), 1):
        check(
            (receipt_dir / f"run-{i}.stdout").read_text().splitlines()
            == [f"{status}: 49 files at {candidate}"],
            "human status",
        )
        check(not (receipt_dir / f"run-{i}.stderr").read_bytes(), "unexpected stderr")
        run = json.loads((receipt_dir / f"run-{i}.json").read_bytes())
        check(run["exit"] == 0 and run["expected_status"] == status, "run status")
        argv = run["argv"]
        check(
            argv[0] == source["source_python"] and argv[1:4] == ["-I", "-B", "-c"],
            "run interpreter",
        )
        for flag, value in (
            ("--sha", source["upstream_pin"]),
            ("--rk", source["upstream_root"]),
            ("--inputs", source["inputs"]),
            ("--input-manifest-sha256", source["input_manifest_sha256"]),
            ("--output-root", str(candidate)),
        ):
            check(
                argv.count(flag) == 1 and argv[argv.index(flag) + 1] == value, "run binding " + flag
            )
        for name in (f"preflight-{i}.json", f"postflight-{i}.json"):
            check(json.loads((receipt_dir / name).read_bytes()) == preflight, name + " drift")
    check(
        json.loads((receipt_dir / "preflight-before.json").read_bytes()) == preflight,
        "initial preflight",
    )
    v.check_manifest(old)
    v.check_generator(old, current=False)
    v.check_manifest(candidate)
    v.check_snapshot_inputs(candidate, check_support=True)
    generator = v.check_generator(candidate, current=True)
    check(generator["environment"] == source["oracle_metadata"], "oracle environment")
    raw_audit = u2_refresh.audit_candidate(candidate)
    check(raw_audit["rows"] == 1008 and raw_audit["adopted"] is False, "strict audit")

    def files(root):
        paths = list(root.rglob("*"))
        check(not any(p.is_symlink() for p in paths), "symlink member")
        return {p.relative_to(root).as_posix(): digest(p) for p in paths if p.is_file()}

    before, after = files(old), files(candidate)
    added, removed = sorted(after.keys() - before.keys()), sorted(before.keys() - after.keys())
    changed = sorted(n for n in before.keys() & after.keys() if before[n] != after[n])
    check(len(before) == 48 and len(after) == 49, "member counts")
    check(added == ["u2-inputs/support-policy.json"] and not removed, "member delta")
    check(
        changed
        == [
            "GENERATOR.json",
            "MANIFEST.json",
            "u2-inputs/SHA256SUMS",
            "u2-inputs/support-files.json",
        ],
        "changed members",
    )
    old_generator = json.loads((old / "GENERATOR.json").read_bytes())
    check(
        {
            k
            for k in generator.keys() | old_generator.keys()
            if generator.get(k) != old_generator.get(k)
        }
        == {"script_sha256"},
        "generator delta",
    )
    saved = files(Path(source["inputs"]))
    check(saved == files(candidate / "u2-inputs"), "saved input copies")
    for subdir in ("components", "model_shapes"):
        check(files(candidate / subdir) == files(candidate / "u2-inputs" / subdir), "outer copies")
    rows = json.loads((candidate / "parity/fixtures.json").read_bytes())
    old_rows = json.loads((old / "parity/fixtures.json").read_bytes())
    check(rows == old_rows and len(rows) == len({r["id"] for r in rows}) == 1008, "all row fields")
    check(
        Counter(r["query"]["phase"] for r in rows) == {"decode": 504, "prefill": 504},
        "phase matrix",
    )
    for a, b in zip(rows, old_rows, strict=True):
        check(
            a["query"] == b["query"]
            and a["counts"] == b["counts"]
            and a["duration_s"] == b["duration_s"],
            "numeric comparison",
        )
        check("vector_ops" not in a["counts"], "unknown channel")
        if a["query"]["phase"] == "decode":
            check(a["counts"]["memory_write_bytes"] is None, "decode unknown writes")
    refusals = json.loads((candidate / "parity/refusals.json").read_bytes())
    check(
        refusals == json.loads((old / "parity/refusals.json").read_bytes()) and len(refusals) == 4,
        "refusals",
    )
    check(
        {(Path(r["component_params_file"]).name, r["compute"], r["kv_cache"]) for r in refusals}
        == {
            ("asic_placeholder.yaml", "bf16", "bf16"),
            ("asic_placeholder.yaml", "fp8", "fp8"),
            ("npu-l4.yaml", "fp16", "fp16"),
            ("npu-l4.yaml", "fp8", "fp8"),
        },
        "refusal matrix",
    )
    pre["source_guard"]()
    print(
        json.dumps(
            dict(
                status="passed; NOT adopted",
                source_commit=source["source_commit"],
                source_tree=source["source_tree"],
                input_manifest_sha256=source["input_manifest_sha256"],
                candidate_manifest_sha256=EXPECTED,
                old_manifest_sha256=source["current_artifact_manifest_sha256"],
                strict_candidate_audit=raw_audit,
                total_candidate_files=len(after),
                unchanged_files=44,
                added=added,
                removed=removed,
                changed=changed,
                file_delta={n: dict(before=before.get(n), after=after[n]) for n in changed + added},
                generator_changed_fields=["script_sha256"],
                nominal_rows_identical=1008,
                refusals_identical=4,
                phase_counts=dict(Counter(r["query"]["phase"] for r in rows)),
                saved_input_files_exact=len(saved),
                numerical_differences=0,
                receipt_hashes=files(receipt_dir),
                source_clean=True,
                producer_oracle_calls="disabled",
                generation="human receipts verified; not rerun",
                physical_native_silicon_validation=False,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    check(sys.flags.isolated and sys.dont_write_bytecode, "use -I -B")
    main()
