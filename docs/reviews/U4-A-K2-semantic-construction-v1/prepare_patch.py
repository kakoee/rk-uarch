"""Construct the proposed protected delta ONLY in an explicitly supplied /tmp Git export."""

import argparse
import difflib
import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent


def prepare(root: Path) -> list[str]:
    root = root.resolve()
    if not root.is_relative_to(Path("/tmp")) or (root / ".git").exists():
        raise ValueError("Only a disposable /tmp export, never a live checkout")
    originals: dict[str, str] = {}

    def edit(name: str, after: str) -> None:
        path = root / name
        originals[name] = path.read_text() if path.exists() else ""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(after)

    name = "contract/uarch_contract/mapped.py"
    source = (root / name).read_text()
    source = source.replace(
        "class ClockSetup(FrozenModel):",
        'class ClockSetup(FrozenModel):\n    """Proposed earliest release; cycles'
        ' run from actual owner grant."""',
    )
    source = source.replace(
        '        "END",\n    ]',
        '        "END",\n        "DEPENDENCY_READY",\n        "OWNER_GRANT",\n      '
        '  "TASK_RELEASE",\n    ]',
    )
    source = source.replace("    ready_ps: U64\n", "    release_ps: U64\n    ready_ps: U64\n")
    source = source.replace(
        '    clock_domain: Literal["core", "noc", "dram"]\n',
        '    clock_domain: Literal["core", "noc", "dram"] | None\n',
    )
    source = source.replace(
        "class CriticalInterval(FrozenModel):\n",
        'class CriticalInterval(FrozenModel):\n    kind: Literal["service", "release_idle"]\n',
    )
    start = source.index("class CriticalInterval(")
    end = source.index("\n\nclass Observed", start)
    fragment = source[start:end].replace(
        "limiting_resource_id: U64", "limiting_resource_id: U64 | None"
    )
    fragment += """

    @model_validator(mode="after")
    def interval_kind(self) -> CriticalInterval:
        require(self.end_ps > self.start_ps, "AttributionMismatch")
        if self.kind == "release_idle":
            require(self.start_ps == 0 and self.predecessor_id is None
                    and self.limiting_resource_id is None and self.category == "overhead",
                    "AttributionMismatch")
        else:
            require(self.limiting_resource_id is not None, "InvalidResource")
        return self


class ClockObservation(FrozenModel):
    job_id: NonEmpty
    domain: Literal["core", "noc", "dram"]
    grant_ps: U64
    n_cycles: U64
    raw_edge_outcome: Literal["success", "TimeOverflow"]
    aligned_start_ps: U64 | None
    completion_ps: U64

    @model_validator(mode="after")
    def alignment_outcome(self) -> ClockObservation:
        require((self.raw_edge_outcome == "success") == (self.aligned_start_ps is not None),
                "IncompleteObservations")
        return self
"""
    source = source[:start] + fragment + source[end:]
    source = source.replace(
        "    jobs: Observed[JobObservation]\n",
        "    jobs: Observed[JobObservation]\n"
        "    clocks: Annotated[Observed[ClockObservation] | Unrepresented,"
        ' Field(discriminator="status")]\n',
    )
    marker = "        else:\n            require(\n                self.owners == canonical_owners"
    addition = """            for setup in self.clock_setup:
                declared = next(j for j in p.task_graph.jobs if j.id == setup.job_id)
                require(isinstance(declared, FixedDelay) and declared.duration_ps == 0,
                        "UnsupportedScope", "clock setup exclusively controls service")
"""
    assert source.count(marker) == 1
    source = source.replace(marker, addition + marker)
    source = source.replace(
        "            and interval.limiting_resource_id in owner_ids,",
        "            and (interval.limiting_resource_id in owner_ids\n"
        '                 if interval.kind == "service" else'
        " interval.limiting_resource_id is None),",
    )
    marker = "    return r\n\n\ndef admit("
    assert source.count(marker) == 1
    source = source.replace(
        marker,
        '    if job.state_model == "fixed_delay/1":\n'
        "        validate_fixed_delay_observations(r, job)\n"
        "    else:\n"
        '        require(all(x.kind == "service" for x in r.observations.critical_path.records),\n'
        '                "AttributionMismatch")\n'
        "        assert isinstance(r.observations.queue_membership, Observed)\n"
        "        require(all(x.clock_domain is not None\n"
        "                    for x in r.observations.queue_membership.records),"
        ' "IncompleteObservations")\n'
        "    return r\n\n"
        + (PACKAGE / "accounting_fragment.py.txt").read_text()
        + "\n\ndef admit(",
    )
    edit(name, source)
    name = "docs/decisions/U0011-the-native-engine-core.md"
    edit(name, (root / name).read_text() + "\n" + (PACKAGE / "adr-addendum.md").read_text())
    amendment = (PACKAGE / "prompt-addendum.txt").read_text() + "\n"
    for name in ("docs/prompts/U-P11a-native-engine-kernel.md", "docs/build-spec.md"):
        s = (root / name).read_text()
        marker = (
            "9. src/rkuarch/engines/native/: the Python side: job writer, subprocess runner, result"
        )
        assert s.count(marker) == 1
        s = s.replace(marker, amendment + marker)
        old = (
            "  Implement items 9–10 and execute every acceptance case at the public "
            "subprocess boundary."
        )
        new = (
            "  Implement items 9–10 and execute every representable acceptance case at the public\n"
            "  subprocess boundary, including all raw clock obligations through"
            " observations.clocks.\n"
            "  Retain all 100 arbitrary Wheel/Arena schedules and sequence/insertion"
            " controls privately;\n"
            "  repeat their representable owner/order laws and reached fault controls publicly.\n"
            "  This explicit exception creates no event-injection input or public"
            " credit for private tests."
        )
        assert s.count(old) == 1
        edit(name, s.replace(old, new))
    edit(
        "contract/tests/mapped/test_k2_semantic_completion.py",
        (PACKAGE / "contract_tests.py.txt").read_text(),
    )
    name = "contract/tests/mapped/test_admission.py"
    s = (root / name).read_text()
    marker = (
        '    j["clock_setup"] = [{"job_id": "a", "domain": "core", "start_ps": 0, "n_cycles": 3}]'
    )
    assert s.count(marker) == 2
    update = "\n".join(
        [
            '    j["mapped_point"]["task_graph"]["jobs"][0]["duration_ps"] = 0',
            '    rehash(j["mapped_point"]["task_graph"], "graph_hash")',
            '    rehash(j["mapped_point"], "payload_hash")',
            '    j["point_hash"] = j["mapped_point"]["payload_hash"]',
            '    j["workload_closure"]["points"] = [copy.deepcopy(j["mapped_point"])]',
            '    j["profile"]["entries"][0]["graph_hash"] ='
            ' j["mapped_point"]["task_graph"]["graph_hash"]',
            '    j["profile"]["entries"][0]["point_hash"] = j["point_hash"]',
            "",
        ]
    )
    before, after = s.rsplit(marker, 1)
    edit(name, before + update + marker + after)
    name = "tests/unit/test_u4_a_mapped_loader.py"
    s = (root / name).read_text()
    old = '    raw["mapped_point"]["task_graph"]["jobs"][0]["duration_ps"] += 1'
    assert s.count(old) == 1
    edit(
        name, s.replace(old, '    raw["mapped_point"]["task_graph"]["jobs"][0]["duration_ps"] = 0')
    )
    (root / ".proposal-originals.json").write_text(json.dumps(originals))
    return list(originals)


def collect(root: Path, out: Path) -> None:
    originals = json.loads((root / ".proposal-originals.json").read_text())
    # Generator outputs also get exact baseline preimages from this export's saved inventory.
    originals.update(json.loads((root / ".schema-originals.json").read_text()))
    patch, entries = [], []
    for name, before in sorted(originals.items()):
        after = (root / name).read_text()
        if before == after:
            continue
        patch.extend(
            difflib.unified_diff(
                before.splitlines(True),
                after.splitlines(True),
                fromfile="a/" + name if before else "/dev/null",
                tofile="b/" + name,
            )
        )
        entries.append(
            dict(
                path=name,
                before_sha256=hashlib.sha256(before.encode()).hexdigest() if before else None,
                after_sha256=hashlib.sha256(after.encode()).hexdigest(),
            )
        )
    out.mkdir(parents=True, exist_ok=True)
    (out / "complete.proposed.patch").write_text("".join(x.rstrip() + "\n" for x in patch))
    (out / "patch-manifest.json").write_text(json.dumps(entries, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--collect", type=Path)
    args = parser.parse_args()
    if args.collect:
        collect(args.root, args.collect)
    else:
        prepare(args.root)
        schemas = {
            str(p.relative_to(args.root)): p.read_text()
            for p in (args.root / "contract/schema/mapped").glob("*.json")
        }
        (args.root / ".schema-originals.json").write_text(json.dumps(schemas))
