"""Coordinator fault injection; illustrative failures, never actual-run evidence."""

import json

from validation.reporting import analytic_report as report


def probe(label, output):
    events = []
    discovery = report.discover(
        report.profile("analytic-l0-smoke"),
        engine=lambda job: output,
        sink=lambda kind, value: events.append(kind),
    )
    result = report.replay(discovery, implementation=report.git_head())
    try:
        report.validate_report(
            result,
            expected_plan=result["plan"],
            expected_corpus=result["corpus"],
            expected_implementation=result["implementation_git_commit"],
            allow_illustration=True,
        )
    except (ValueError, TypeError) as exc:
        validation = {"accepted": False, "reason": type(exc).__name__ + ": " + str(exc)}
    else:
        validation = {"accepted": True}
    calls = [call for case in discovery.cases for call in case["calls"]]
    return {
        "case": label,
        "discovery_calls": len(calls),
        "error_calls_without_diagnostic": sum(
            call["state"] == "error" and call["diagnostic_hash"] is None for call in calls
        ),
        "call_started": events.count("call_started"),
        "call_finished": events.count("call_finished"),
        "validation": validation,
        "reduction": result["reduction"],
    }


if __name__ == "__main__":
    for name, value in (
        ("serializable_malformed_control", {}),
        ("nonfinite_output", {"duration_ps": float("nan")}),
        ("non_json_output", object()),
    ):
        print(json.dumps(probe(name, value), sort_keys=True), flush=True)
