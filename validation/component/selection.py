"""Prospective component result assertions; bind to the released public runner at first use.

This module never launches K2, generates authority, or writes native receipts. All required
six-way calls, mutation/restoration calls, outcomes and raw bytes belong in the coordinator's
future genuinely authorized B execution ledger. Missing calls remain not_run.
"""

from fractions import Fraction
from typing import Any

from uarch_contract.mapped import MappedEngineJob, MappedEngineResult

from validation.component.checks import need
from validation.component.observations import consume


def assert_case(
    job: MappedEngineJob,
    result: MappedEngineResult,
    item: dict[str, Any],
    observation_contract: dict[str, Any],
) -> None:
    b, p, expected = item["bundle"], item["profile"], item["expected"]
    need(
        job.bundle_hash == b["bundle_hash"] and job.admission.profile_hash == p["profile_hash"],
        "case input binding",
    )
    need(expected["outcome"] == "success", "expected refusal cannot consume success")
    consume(job, result.model_dump(mode="json"), observation_contract)
    raw = result.model_dump(mode="json")
    for field in ("duration_ps",):
        if field in expected:
            need(raw[field] == expected[field], "literal " + field)
    for key, field in [("useful_ops", "matrix_ops")]:
        if key in expected:
            need(raw["counts"][field] == expected[key], "literal " + key)
    if "issued_ops" in expected:
        need(raw["work_counts"]["issued_matrix_ops"] == expected["issued_ops"], "issued literal")
    for field in (
        "read_payload_bytes",
        "write_payload_bytes",
        "read_transaction_bytes",
        "write_transaction_bytes",
        "unicast_payload_bytes",
    ):
        if field in expected:
            need(raw["traffic_counts"][field] == expected[field], "literal " + field)
    if expected.get("hbm_payload_bytes") == 0:
        need(
            raw["traffic_counts"]["read_payload_bytes"] == 0
            and raw["traffic_counts"]["write_payload_bytes"] == 0,
            "resident HBM",
        )
    if "useful_floor_ps" in expected:
        need(raw["duration_ps"] >= expected["useful_floor_ps"], "independent component floor")
    if "attribution_ps" in expected:
        need(raw["attribution_ps"] == expected["attribution_ps"], "causal literal assignment")
    obs = raw["observations"]
    if "job_times_ps" in expected:
        times = {x["job_id"]: [x["start_ps"], x["end_ps"]] for x in obs["jobs"]["records"]}
        need(times == expected["job_times_ps"], "independent overlap literal")
    dma = sorted(obs["dma"]["records"], key=lambda x: x["request_id"])
    for field in ("issue_ps", "complete_ps"):
        if field in expected:
            need([x[field] for x in dma] == expected[field], "literal " + field)
    owners = {x.owner_id: x.resource for x in job.owners}
    channels = sorted(
        [
            x
            for x in obs["resource_intervals"]["records"]
            if owners[x["owner_id"]].startswith("channel:")
            and x["service_end_ps_ratio"] is not None
        ],
        key=lambda x: Fraction(
            x["service_end_ps_ratio"]["numerator"], x["service_end_ps_ratio"]["denominator"]
        ),
    )
    if "channel_end_ps" in expected:
        need([x["end_ps"] for x in channels] == expected["channel_end_ps"], "channel ceil")
    if "channel_end_ratios" in expected:
        need(
            [
                [x["service_end_ps_ratio"]["numerator"], x["service_end_ps_ratio"]["denominator"]]
                for x in channels
            ]
            == expected["channel_end_ratios"],
            "rational service carry",
        )
    if "crossings_ps" in expected:
        port, arrival, latency, channel, response, done = expected["crossings_ps"]
        clocks = obs["clocks"]
        need(clocks["status"] == "observed", "crossing clocks")
        rows = clocks["records"]
        need(
            any(
                x["domain"] == "noc" and x["n_cycles"] == 4 and x["completion_ps"] == arrival
                for x in rows
            ),
            "request edge/domain",
        )
        need(
            any(
                x["domain"] == "dram" and x["n_cycles"] == 48 and x["completion_ps"] == latency
                for x in rows
            ),
            "DRAM edge/domain",
        )
        need(len(channels) == 1 and channels[0]["end_ps"] == channel, "channel boundary")
        need(
            any(
                x["domain"] == "noc" and x["n_cycles"] == 4 and x["completion_ps"] == response
                for x in rows
            ),
            "response edge/domain",
        )
        need(len(dma) == 1 and dma[0]["complete_ps"] == done, "commit/ack edge")
        if port:
            need(
                any(
                    x["domain"] == "core" and x["n_cycles"] == 1 and x["completion_ps"] == port
                    for x in rows
                ),
                "write port",
            )


def assert_replays(outputs: dict[tuple[str, int], bytes]) -> None:
    need(
        set(outputs) == {(mode, run) for mode in ("debug", "release") for run in range(3)},
        "six actual replay calls required",
    )
    need(len(set(outputs.values())) == 1, "canonical result determinism")
