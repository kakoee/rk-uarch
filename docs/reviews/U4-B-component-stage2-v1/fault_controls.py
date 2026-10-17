"""Private behavioral controls; fingerprints excluded, exact source restored in finally."""

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
python = sys.executable
runner = Path(__file__).with_name("isolated.py")
(root / "b-logs").mkdir(exist_ok=True)
# Group by invariant, not implementation line. Identity tests are deliberately absent.
experiments = [
    (
        "attribution",
        ["activity category/domain"],
        "test_consistent_checker_forgery[M1-activity category/domain]",
    ),
    ("owner", ["activity owner"], "test_consistent_checker_forgery[M2-activity owner]"),
    (
        "causes",
        ["complete eligible causes"],
        "test_consistent_checker_forgery[V2-complete eligible causes]",
    ),
    (
        "false-credit",
        ["complete eligible causes"],
        "test_consistent_checker_forgery[V1-complete eligible causes]",
    ),
    (
        "off-chain",
        ["complete eligible causes"],
        "test_consistent_checker_forgery[M3-complete eligible causes]",
    ),
    (
        "port-order",
        ["port FIFO tie"],
        "test_consistent_checker_forgery[port_reverse-port FIFO tie]",
    ),
]
for name, detail in [
    ("duration", "mechanism duration"),
    ("carry", "rational channel carry/readiness"),
    ("rational", "channel mechanism"),
    ("busy", "busy union"),
    ("null_floor", "fidelity/null floor"),
    ("fidelity", "fidelity/null floor"),
    ("diagnostic", "unmodeled diagnostics"),
    ("unrepresented", "unrepresented paths"),
    ("critical", "unrepresented critical predecessor"),
    ("job_owner", "job owner binding"),
    ("release", "job release binding"),
    ("blockers", "unrepresented job blockers"),
    ("event", "event transition binding"),
    ("queue_clock", "nonclocked exact binding"),
]:
    experiments.append((name, [detail], f"test_mechanism_and_field_forgery[{name}-{detail}]"))
experiments = [x for x in experiments if x[0] != "duration"]
experiments += [
    (
        "duration-joint",
        ["mechanism duration", "clock mechanism binding"],
        "test_mechanism_and_field_forgery[duration-mechanism duration]",
    ),
    (
        "readiness",
        ["service readiness after alignment"],
        "test_transition_and_population_forgery[readiness-service readiness after alignment]",
    ),
    (
        "channel-order",
        ["channel FIFO tie"],
        "test_transition_and_population_forgery[channel_fifo-channel FIFO tie]",
    ),
    (
        "partition",
        ["mechanism causal partition"],
        "test_transition_and_population_forgery[critical_partition-mechanism causal partition]",
    ),
    (
        "channel-population",
        ["channel population lifecycle"],
        "test_transition_and_population_forgery[channel_population-channel population lifecycle]",
    ),
    (
        "ordinary-population",
        ["ordinary queue exact binding"],
        "test_transition_and_population_forgery[ordinary_population-ordinary queue exact binding]",
    ),
    (
        "occupancy-join",
        ["required occupancy", "occupied row inventory", "busy union"],
        "test_consistent_checker_forgery[M4a-required occupancy]",
    ),
    (
        "hidden-channel-law",
        ["required occupancy", "occupied row inventory", "busy union", "channel integer mechanism"],
        "test_consistent_checker_forgery[M4b-channel integer mechanism]",
    ),
    (
        "hidden-port-overlap",
        [
            "required occupancy",
            "occupied row inventory",
            "busy union",
            "exclusive mechanism intervals",
            "port eligible grant",
        ],
        "test_consistent_checker_forgery[port_overlap-exclusive mechanism intervals]",
    ),
    ("attribution-totals", ["causal attribution totals"], "test_causal_attribution_totals"),
    ("unicast-input", ["unicast request binding"], "test_unicast_request_inventory_and_ownership"),
    (
        "allocation-lifetime",
        ["allocation access lifetime", "accumulator lifetime mechanism"],
        "test_transition_and_population_forgery[allocation_lifetime-allocation access lifetime]",
    ),
]
paths = [
    root / "validation/component" / name
    for name in ["observations_v2.py", "transition_checks.py", "phase_laws.py"]
]
originals = {p: p.read_bytes() for p in paths}
results = []
for name, details, test in experiments:
    changed = []
    try:
        for p, data in originals.items():
            s = data.decode()
            lines = s.splitlines(keepends=True)
            offsets = [0]
            for line in lines:
                offsets.append(offsets[-1] + len(line))
            edits = []
            for node in ast.walk(ast.parse(s)):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "need"
                    and len(node.args) > 1
                    and isinstance(node.args[1], ast.Constant)
                    and node.args[1].value in details
                ):
                    n = node.args[0]
                    edits.append(
                        (
                            offsets[n.lineno - 1] + n.col_offset,
                            offsets[n.end_lineno - 1] + n.end_col_offset,
                        )
                    )
            for start, end in sorted(edits, reverse=True):
                s = s[:start] + "True" + s[end:]
            if edits:
                p.write_text(s)
                changed.append(str(p.relative_to(root)))
        assert changed, name
        command = [
            python,
            "-I",
            str(runner),
            str(root),
            "pytest",
            "-q",
            "validation/component/test_consistent_observations.py::" + test,
        ]
        proc = subprocess.run(command, text=True, capture_output=True)
        log = proc.stdout + proc.stderr
        (root / "b-logs" / f"{name}-removed.log").write_text(log)
        killed = proc.returncode == 1 and "DID NOT RAISE" in log
        results.append(
            dict(
                invariant=name,
                guards=details,
                paths=changed,
                test=test,
                exit_code=proc.returncode,
                unsafe_acceptance=killed,
                log_sha256=hashlib.sha256(log.encode()).hexdigest(),
            )
        )
        print(name, killed, flush=True)
    finally:
        for p, data in originals.items():
            p.write_bytes(data)
            assert p.read_bytes() == data
    proc = subprocess.run(command, text=True, capture_output=True)
    log = proc.stdout + proc.stderr
    (root / "b-logs" / f"{name}-restored.log").write_text(log)
    results[-1].update(
        restored_source_sha256={
            str(p.relative_to(root)): hashlib.sha256(data).hexdigest()
            for p, data in originals.items()
        },
        restored_exit_code=proc.returncode,
        exact_bytes_restored=True,
        restored_log_sha256=hashlib.sha256(log.encode()).hexdigest(),
    )
    assert proc.returncode == 0, (name, log)
(root / "b-logs/final-restoration.json").write_text(json.dumps(results, indent=2) + "\n")
assert all(x["unsafe_acceptance"] for x in results)
