"""RR-C1 diagnostic over actual saved tables; production remains unchanged."""

import difflib
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import yaml
from uarch_contract.hardware import HardwareSpec, sourced_leaves
from uarch_contract.hashing import content_hash, spec_hash

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RECEIVED = ROOT.parent / "rk-uarch-u2-integration/docs/reviews/U2-adoption-v1-execution/runtime"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def conditions(hardware, *, canonical_order=False):
    leaves = sourced_leaves(hardware)
    if canonical_order:
        leaves = sorted(leaves, key=lambda item: item[0])
    return [
        dict(path=p, value=v.model_dump(mode="json")) for p, v in leaves if v.kind == "stipulation"
    ]


def main():
    out = Path(json.loads((HERE / "output-location.json").read_text())["root"])
    original = json.loads((RECEIVED / "table.json").read_bytes())
    replay = json.loads((out / "report/table.json").read_bytes())
    hardware = HardwareSpec.model_validate(
        yaml.safe_load((ROOT / "hw/designs/npu-l4.yaml").read_text())
    )
    saved = json.loads((RECEIVED / "physical-capture.json").read_bytes())
    bundle = saved["artifacts"][original["artifacts"]["prepared_bundle_hash"]]
    loaded = HardwareSpec.model_validate(bundle["hardware_spec"])
    assert hardware == loaded
    assert spec_hash(hardware) == spec_hash(loaded) == original["hardware_spec_hash"]
    a, b = conditions(hardware), conditions(loaded)
    assert a == original["provenance"]["conditional_on"]
    assert b == replay["provenance"]["conditional_on"] and a != b
    assert {c["path"]: c["value"] for c in a} == {c["path"]: c["value"] for c in b}
    assert original["table_hash"] == content_hash(original, exclude=("table_hash",))
    assert replay["table_hash"] == content_hash(replay, exclude=("table_hash",))
    normalized = []
    for table in (original, replay):
        value = deepcopy(table)
        value["provenance"]["conditional_on"].sort(key=lambda c: c["path"])
        value["table_hash"] = content_hash(value, exclude=("table_hash",))
        normalized.append(value)
    assert normalized[0] == normalized[1]
    assert conditions(hardware, canonical_order=True) == conditions(loaded, canonical_order=True)
    # Exact review proposal only. No production file, table or captured input is rewritten.
    relative = "src/rkuarch/table/build.py"
    old = (ROOT / relative).read_text()
    needle = "                for p, v in sourced_leaves(b.hardware_spec)\n"
    assert old.count(needle) == 1
    new = old.replace(
        needle,
        "                for p, v in sorted(sourced_leaves(b.hardware_spec), "
        "key=lambda item: item[0])\n",
    )
    (HERE / "RR-C1-proposed.patch").write_text(
        "".join(
            difflib.unified_diff(
                old.splitlines(True),
                new.splitlines(True),
                fromfile="a/" + relative,
                tofile="b/" + relative,
            )
        )
    )
    support = json.loads(
        (
            ROOT
            / "contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963"
            / "u2-inputs/support-files.json"
        ).read_text()
    )
    assert support[relative] == digest(ROOT / relative)
    result = dict(
        finding="RR-C1",
        status="reproduced; source proposal unapplied",
        cause=(
            "build_table preserves sourced_leaves dictionary insertion order in "
            "conditional_on array; canonical saved JSON changes mapping order while "
            "preserving input identity"
        ),
        received_table_hash=original["table_hash"],
        replayed_table_hash=replay["table_hash"],
        hardware_spec_hash=spec_hash(hardware),
        prepared_bundle_hash=original["artifacts"]["prepared_bundle_hash"],
        same_hardware_and_condition_mapping=True,
        condition_count=len(a),
        order_changes=[
            dict(index=k, before=x["path"], after=y["path"])
            for k, (x, y) in enumerate(zip(a, b, strict=True))
            if x != y
        ],
        all_other_table_content_equal=True,
        proposed_sorted_table_hash=normalized[0]["table_hash"],
        proposed_sort_two_representation_control=True,
        path=relative,
        old_sha256=digest(ROOT / relative),
        proposed_sha256=hashlib.sha256(new.encode()).hexdigest(),
        generator_bound_support_member=True,
        lifecycle=(
            "Changes support84: strict old-support input verification would reject. "
            "Requires A/coordinator-reviewed correction and explicit source/input/artifact "
            "lifecycle decision before applying; no source edit, generation or adoption "
            "performed."
        ),
        required_regression=(
            "Build complete tables from actual H1 YAML-order capture and canonical "
            "serialized/imported capture, require equal table, provenance, hashes and "
            "bytes; repeat report modes, RenderSpecs and producer-disabled replay on the "
            "selected reviewed inputs."
        ),
    )
    (HERE / "RR-C1.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
