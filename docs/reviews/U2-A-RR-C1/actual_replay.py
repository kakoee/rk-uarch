"""Received actual 24-row H1 result replay; no new engine execution or measurement."""
import hashlib
import importlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import yaml
from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import canonical_json, spec_hash

from rkuarch.table.artifacts import load_verified_report_inputs
from rkuarch.table.build import CapturedWork, build_table
from rkuarch.workload.prepared import load_prepared_input
from tests.integration.test_u2_a_condition_order import expected_conditions

OUT = Path("docs/reviews/U2-A-RR-C1")
REPORT = Path("/tmp/u2-b-real-report-exits-v1-xn5pjr8z/outputs/report/table.json")
started = time.monotonic()
record = dict(
    classification="Actual received results/real context replay, not new engine or hardware execution",
    argv=sys.argv, cwd=str(Path.cwd()),
    environment={k: os.environ.get(k) for k in ("PYTHONPATH", "PYTHONDONTWRITEBYTECODE")},
    source_sha256=hashlib.sha256(Path("src/rkuarch/table/build.py").read_bytes()).hexdigest(),
    harness_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    tests_sha256=hashlib.sha256(Path("tests/integration/test_u2_a_condition_order.py").read_bytes()).hexdigest(),
    received_report=str(REPORT),
    received_report_file_sha256=hashlib.sha256(REPORT.read_bytes()).hexdigest(),
    phases=[], status="running",
)


def save():
    record["elapsed_s"] = time.monotonic() - started
    (OUT / "actual-replay.json").write_text(json.dumps(record, indent=2) + "\n")


def phase(name, fn):
    t = time.monotonic()
    result = fn()
    record["phases"].append(dict(name=name, seconds=time.monotonic()-t))
    save()
    print(name, record["phases"][-1]["seconds"], flush=True)
    return result


def disabled(*args, **kwargs):
    raise AssertionError("preparation/analytic producer called during captured-result replay")


for module, names in (
    ("rkuarch.workload.prepare", ("prepare",)),
    ("rkuarch.engines.analytic.core", ("run_analytic",)),
    ("rkuarch.workload.prepared", ("execute_prepared_point",)),
    ("rkuarch.table.build", ("capture", "execute_prepared_point")),
):
    for name in names:
        setattr(importlib.import_module(module), name, disabled)
try:
    save()
    v = phase("public_offline_loader", lambda: load_verified_report_inputs(REPORT))
    hw = HardwareSpec.model_validate(yaml.safe_load(Path("hw/designs/npu-l4.yaml").read_bytes()))
    assert hw == v.hardware and spec_hash(hw) == spec_hash(v.hardware)
    saved = Path(tempfile.mkdtemp(prefix="u2-a-rr-c1-")) / "prepared.json"
    saved.write_text(canonical_json(v.bundle))
    bundle = phase("public_saved_prepared_loader", lambda: load_prepared_input(saved))
    assert bundle == v.bundle
    record["saved_prepared"] = str(saved)
    record["saved_prepared_sha256"] = hashlib.sha256(saved.read_bytes()).hexdigest()
    yaml_work = CapturedWork(bundle.model_copy(update={"hardware_spec": hw}), v.assumptions,
                             v.request, v.derivation, v.jobs, v.results)
    saved_work = CapturedWork(bundle, v.assumptions, v.request, v.derivation, v.jobs, v.results)
    def build(c):
        return build_table(c, context=v.context, model_card=v.model_card, artifacts=v.artifacts)
    a = phase("public_yaml_order_build", lambda: build(yaml_work))
    b = phase("public_canonical_saved_build", lambda: build(saved_work))
    assert len(a.table.rows) == len(b.table.rows) == 24
    assert a.table.rows == b.table.rows == v.table.rows
    expected = expected_conditions(hw.model_dump(mode="json"))
    assert len(expected) == 59
    for table in (a.table, b.table):
        conditions = table.provenance.conditional_on
        assert len(conditions) == len(expected)
        assert [c.path for c in conditions] == sorted(expected)
        assert {c.path: c.value.model_dump(mode="json") for c in conditions} == expected
    assert a.table.provenance == b.table.provenance
    assert a.table.table_hash == b.table.table_hash
    assert a.table.table_hash == "sha256:200ca0f703feb341e3871ad3a1f897ac45cb1e42f270d10384ea31cdcafbd554"
    left, right = canonical_json(a.table).encode(), canonical_json(b.table).encode()
    assert left == right
    assert a == b
    # Historical table differs only in list ordering and its dependent identity.
    old = v.table.model_dump(mode="json")
    current = a.table.model_dump(mode="json")
    old_conditions = old["provenance"].pop("conditional_on")
    new_conditions = current["provenance"].pop("conditional_on")
    old.pop("table_hash"); current.pop("table_hash")
    assert old == current
    assert sorted(old_conditions, key=lambda c: c["path"]) == new_conditions
    record.update(status="passed", rows=24, conditions=59, rows_equal_to_received=True,
                  full_provenance_equal=True, exact_condition_membership_values=True,
                  complete_table_bytes_equal=True, complete_package_equal=True,
                  yaml_table_hash=a.table.table_hash, saved_table_hash=b.table.table_hash,
                  received_table_hash=v.table.table_hash,
                  canonical_table_sha256=hashlib.sha256(left).hexdigest(), canonical_table_bytes=len(left),
                  hardware_hash=spec_hash(hw), bundle_hash=bundle.bundle_hash,
                  context_hash=v.context.context_hash, producers_disabled=True,
                  result_hashes=[r.result_hash for r in v.results],
                  only_historical_difference="conditional_on ordering and table_hash")
    save()
    print("PASS: 24 rows, 59 conditions, complete table bytes and captured-result replay", flush=True)
except BaseException as exc:
    record.update(status="failed", error=repr(exc)); save(); raise
