"""Remove only B's terminal-before-reservation predicate; restore exact bytes in finally."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

source, runs, a7, out = map(Path, sys.argv[1:])
out.mkdir(exist_ok=False)
python = "/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python"
runner = "/tmp/u4-b-stage2-review-01/probes/runner.py"
consumer = Path(__file__).with_name("consume.py")
p = source / "validation/component/issue_checks.py"
original = p.read_bytes()
guard = b"        and terminal_ordinals[key] < reservation_cursor\n"
assert original.count(guard) == 1
report = {"guard": guard.decode().strip(), "preimage": hashlib.sha256(original).hexdigest()}
try:
    p.write_bytes(original.replace(guard, b""))
    report["fault_postimage"] = hashlib.sha256(p.read_bytes()).hexdigest()
    subprocess.run(
        [
            python,
            "-I",
            runner,
            str(source),
            "script",
            str(consumer),
            str(source),
            str(runs),
            str(a7),
            str(out / "fault.json"),
        ],
        check=True,
        capture_output=True,
    )
    cases = {x["case"]: x for x in json.loads((out / "fault.json").read_text())["cases"]}
    assert cases["A7-post-reservation-credit"]["independent"] == "pass"
    assert cases["sr-v3-debug"]["independent"] == "pass"
    assert cases["cc0-v3-debug"]["independent"] == "CheckFailure: complete eligible causes"
    report["unsafe_acceptance"] = (
        "A7; same-time terminal is after grant but before alignment dispatch"
    )
    report["valid_control"] = (
        "sr-v3 passes; mixed cc0-v3 regresses to false refusal under timestamp-only fault"
    )
finally:
    p.write_bytes(original)
assert p.read_bytes() == original
subprocess.run(
    [
        python,
        "-I",
        runner,
        str(source),
        "script",
        str(consumer),
        str(source),
        str(runs),
        str(a7),
        str(out / "restored.json"),
    ],
    check=True,
    capture_output=True,
)
cases = {x["case"]: x for x in json.loads((out / "restored.json").read_text())["cases"]}
assert (
    cases["A7-post-reservation-credit"]["independent"] == "CheckFailure: complete eligible causes"
)
assert all(
    cases[n + "-" + m]["independent"] == "pass"
    for n in ["cc0-v3", "cc-v3", "sr-v3"]
    for m in ["debug", "release"]
)
report["restored_sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
report["structural_layer"] = (
    "Recorded separately: old structural consumer still accepts A7; "
    "this fault targets only independent defense"
)
(out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
