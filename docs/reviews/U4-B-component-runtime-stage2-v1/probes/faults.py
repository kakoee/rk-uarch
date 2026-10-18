"""Bounded private source faults, real behavioral regression failures, exact restoration."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

root, out = map(Path, sys.argv[1:])
assert root.is_relative_to("/tmp") and out.is_relative_to("/tmp")
runner = "/tmp/u4-b-runtime-review-01/probes/runner.py"
python = "/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python"
base = "validation/component/"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(label, test):
    p = subprocess.run(
        [python, "-I", runner, str(root), "pytest", "-q", base + test], capture_output=True
    )
    (out / (label + ".log")).write_bytes(p.stdout + p.stderr)
    return p.returncode


specs = [
    (
        "B-F1-exact-envelope",
        "runtime_evidence.py",
        '    need(value == expected, "exact intended refusal envelope")',
        '    need(True, "exact intended refusal envelope")',
        "test_runtime_campaign.py::test_exact_refusal_rejects_borrowed_pre_and_post_dispatch_envelopes",
    ),
    (
        "B-F3-matrix-order",
        "matrix_order.py",
        'row["start_ps"] == max(ready, previous)',
        "True",
        "test_matrix_order.py::test_matrix_equal_ready_tie_and_wrong_order",
    ),
    (
        "B-F9-closed-literals",
        "runtime_checks.py",
        "    check_extended_literals(job, result, expected)",
        "    pass  # private disconnected literal wrapper",
        "test_runtime_checks.py::test_unknown_literal_is_not_silently_ignored",
    ),
    (
        "B-F4-byte-consumption",
        "runtime_campaign.py",
        "outcome = consume_attempt(raw, rows[case], slot, acceptance)",
        'outcome = rows[case]["expected_code"]',
        (
            "test_runtime_campaign.py::"
            "test_negative_campaign_requires_intended_guard_and_bound_zero_entry"
            "[wrong-guard-intended refusal]"
        ),
    ),
    (
        "B-F6-durable-replay",
        "runtime_campaign.py",
        "initial = replay_admission(output, initial_refs, rows[case], acceptance)",
        "initial = None",
        "test_runtime_campaign.py::test_campaign_rejects_and_preserves_failed_group[missing-receipt-FileNotFoundError]",
    ),
]
# Identity guard removal is separately labelled. Sources/pins still agree in synthetic
# controls, so a source mismatch is not counted as the behavioral regression.
s = (root / base / "runtime_checks.py").read_text()
a = s.index("    need(\n        admitted[")
b = s.index("    model =", a)
specs.append(
    (
        "B-F7-inventory-binding",
        "runtime_checks.py",
        s[a:b],
        "",
        "test_runtime_checks.py::test_separately_frozen_input_refuses_consistent_foreign_pair",
    )
)
s = (root / base / "runtime_campaign.py").read_text()
marker = "                    record = dict(\n"
start = s.index(marker)
end = s.index("                    verify_setup()\n                    record.update", start)
old = s[start:end]
line = "                    outcome = consume_attempt(raw, rows[case], slot, acceptance)\n"
assert old.count(line) == 1
new = line + old.replace(line, "")
specs.append(
    (
        "B-F5-retain-before-validate",
        "runtime_campaign.py",
        old,
        new,
        "test_runtime_campaign.py::test_campaign_rejects_and_preserves_failed_group[unparseable-JSONDecodeError]",
    )
)
reports = []
for label, name, old, new, test in specs:
    path = root / base / name
    original = path.read_bytes()
    assert original.decode().count(old) == 1
    if (out / (label + "-restored.log")).exists():
        assert "passed" in (out / (label + "-control.log")).read_text()
        assert "failed" in (out / (label + "-fault.log")).read_text()
        assert "passed" in (out / (label + "-restored.log")).read_text()
        reports.append(
            dict(
                finding=label,
                path=base + name,
                pre_sha256=sha(original),
                fault_sha256=sha(original.decode().replace(old, new, 1).encode()),
                restored_sha256=sha(original),
                control_exit=0,
                fault_exit=1,
                restored_exit=0,
                test=test,
                reused_completed_controls=True,
                logs=[label + "-" + x + ".log" for x in ("control", "fault", "restored")],
            )
        )
        continue
    before = run(label + "-control", test)
    assert before == 0, (label, "control")
    try:
        path.write_text(original.decode().replace(old, new, 1))
        fault_hash = sha(path.read_bytes())
        fault = run(label + "-fault", test)
        assert fault != 0, (label, "ineffective fault")
    finally:
        path.write_bytes(original)
    assert path.read_bytes() == original
    restored = run(label + "-restored", test)
    assert restored == 0, (label, "restoration")
    reports.append(
        dict(
            finding=label,
            path=base + name,
            pre_sha256=sha(original),
            fault_sha256=fault_hash,
            restored_sha256=sha(path.read_bytes()),
            control_exit=before,
            fault_exit=fault,
            restored_exit=restored,
            test=test,
            distinction="identity binding"
            if label.startswith("B-F7")
            else "behavioral acceptance/evidence retention",
            logs=[label + "-" + x + ".log" for x in ("control", "fault", "restored")],
        )
    )
(out / "fault-restoration.json").write_text(json.dumps(reports, indent=2) + "\n")
print(json.dumps(reports, indent=2))
