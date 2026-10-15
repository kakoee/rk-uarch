"""Author two literal proposal inputs; no mapper, workload producer or oracle calls.

Run only with the final proposed M carrier importable from a disposable export.
"""

import copy
import hashlib
import json
from pathlib import Path

from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import content_hash, spec_hash
from uarch_contract.mapped import admit

PACKAGE = Path(__file__).resolve().parent


def seal(value, field):
    value[field] = content_hash(value, exclude=(field,))
    return value


def buffer(name, space, offset, *, producer=None, consumers=(), resident=False):
    return dict(
        id=name,
        space=space,
        size_bytes=256,
        alignment_bytes=256,
        core_id=0 if space == "sram" else None,
        channel_id=None,
        offset_bytes=offset,
        bank=0 if space == "sram" else None,
        op_id=None,
        operand=None,
        initial_residency="preloaded" if resident else "uninitialized",
        producer_id=producer,
        final_consumer_ids=list(consumers),
        slot_index=None,
    )


def region(name):
    return dict(buffer_id=name, offset_bytes=0, size_bytes=256)


def dma(name, direction, source, destination, channel):
    return dict(
        kind="dma",
        id=name,
        op_id=None,
        dma_engine_id=0,
        direction=direction,
        source=region(source),
        destination=region(destination),
        fragments=[
            dict(
                request_id=name + ".r0",
                source_offset_bytes=0,
                destination_offset_bytes=0,
                payload_bytes=256,
                transaction_bytes=256,
                channel_id=channel,
                route_id="r3",
            )
        ],
    )


def author(export):
    inputs = export / "contract/fixtures/mapped"
    original = json.loads((inputs / "transport.json").read_text())
    registry = json.loads((inputs / "registry.json").read_text())
    artifacts = {}
    for case in ("D02", "D14"):
        bundle = copy.deepcopy(original)
        bundle["producer"] = dict(
            name="B-literal-proposal-inputs",
            version="2",
            implementation_hash="sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        )
        point = bundle["points"][0]
        point.update(
            point_id=case,
            identity=dict(kind="fixture", fixture_id=case),
            initial_state="fixture_resident",
        )
        graph = point["task_graph"]
        route = dict(
            id="r3", noc_index=0, source_core_id=0, destination_core_id=3, core_ids=[0, 1, 3]
        )
        if case == "D02":
            graph.update(
                buffers=[
                    buffer("h", "hbm", 1536, producer="w"),
                    buffer("s", "sram", 0, consumers=["w"], resident=True),
                ],
                jobs=[dma("w", "write", "s", "h", 6)],
                routes=[route],
                dependencies=[],
            )
        else:
            spec = bundle["hardware_spec"]
            spec["id"] = "u4-b-d14-zero-hop-proposed"
            leaf = spec["clock_domains"]["noc"]["freq_hz"]
            leaf.update(
                value=1200000000.0,
                rationale="Verification-only proposed design: expose zero-hop alignment at "
                "a core-port completion that is not a NoC edge; not a chip claim.",
            )
            bundle["hardware_spec_hash"] = spec_hash(HardwareSpec.model_validate(spec))
            graph.update(
                buffers=[
                    buffer("h0", "hbm", 1536, consumers=["a"], resident=True),
                    buffer("h1", "hbm", 1792, consumers=["b"], resident=True),
                    buffer("rd0", "sram", 512, producer="a"),
                    buffer("rd1", "sram", 768, producer="b"),
                    buffer("sd", "sram", 256, producer="c"),
                    buffer("ss", "sram", 0, consumers=["c"], resident=True),
                ],
                jobs=[
                    dma("a", "read", "h0", "rd0", 6),
                    dma("b", "read", "h1", "rd1", 7),
                    dict(
                        kind="noc_transfer",
                        id="c",
                        op_id=None,
                        source=region("ss"),
                        destination=region("sd"),
                        payload_bytes=256,
                        route_id="r0",
                        multicast=False,
                    ),
                ],
                routes=[
                    dict(
                        id="r0", noc_index=0, source_core_id=0, destination_core_id=0, core_ids=[0]
                    ),
                    route,
                ],
                dependencies=[dict(before="b", after="c")],
            )
            registry["test_only_specs"] = [
                dict(
                    hardware_spec_hash=bundle["hardware_spec_hash"],
                    rationale="D14 nonedge zero-hop control; proposed design, verification only",
                )
            ]
        seal(graph, "graph_hash")
        seal(point, "payload_hash")
        profile = dict(
            format="uarch-native-test-profile/1",
            semantics_revision="U0011-stage2/1",
            owner="Lane B agent proposal; human acceptance pending",
            entries=[
                dict(
                    case_id=case,
                    checkpoint="B",
                    scope="transport_fixture",
                    initial_state="fixture_resident",
                    priming_iterations=0,
                    hardware_spec_hash=bundle["hardware_spec_hash"],
                    hardware_spec=bundle["hardware_spec"],
                    frequency_ratio=1.0,
                    freq_hz=dict(
                        core=10**9, noc=1200000000 if case == "D14" else 10**9, dram=10**9
                    ),
                    graph_hash=graph["graph_hash"],
                    point_hash=point["payload_hash"],
                    allowed_job_kinds=["dma", "noc_transfer"] if case == "D14" else ["dma"],
                    expected_outcome="success",
                    seed=0,
                    case_selection_revision="B-SRAM-inputs/2",
                    clock_setup_hash=content_hash([]),
                )
            ],
        )
        seal(profile, "profile_hash")
        bundle["admission"].update(case_id=case, profile_hash=profile["profile_hash"])
        seal(bundle, "bundle_hash")
        artifacts[case] = dict(bundle=bundle, profile=profile)
    seal(registry, "registry_hash")
    identities = {"registry_hash": registry["registry_hash"], "cases": {}}
    out = PACKAGE / "fixtures"
    out.mkdir(exist_ok=True)
    for case, item in artifacts.items():
        # Test-host constants are selected outside admit; they are not human authority.
        admit(
            item["bundle"],
            invocation="test",
            checkpoint="B",
            registry=registry,
            profile=item["profile"],
            trusted_registry_hash=registry["registry_hash"],
            trusted_profile_hash=item["profile"]["profile_hash"],
        )
        b, p = item["bundle"], item["bundle"]["points"][0]
        identities["cases"][case] = dict(
            bundle_hash=b["bundle_hash"],
            point_hash=p["payload_hash"],
            graph_hash=p["task_graph"]["graph_hash"],
            profile_hash=item["profile"]["profile_hash"],
            hardware_spec_hash=b["hardware_spec_hash"],
        )
        for kind, value in item.items():
            (out / f"{case}.{kind}.json").write_text(
                json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
            )
    (out / "registry.json").write_text(
        json.dumps(registry, sort_keys=True, separators=(",", ":")) + "\n"
    )
    (PACKAGE / "fixture-identities.json").write_text(json.dumps(identities, indent=2) + "\n")


if __name__ == "__main__":
    import sys

    author(Path(sys.argv[1]).resolve())
