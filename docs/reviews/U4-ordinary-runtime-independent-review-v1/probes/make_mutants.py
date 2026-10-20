"""Reviewer job mutants: every integrity hash is recomputed so the targeted semantic law fires.

Usage: RUNTIME_PYTHON -I make_mutants.py RECONSTRUCTED_TREE INPUT_DIR OUT_DIR
Writes OUT_DIR/<name>.json (raw bytes as a user could supply them) and OUT_DIR/manifest.json.
Expected codes are the reviewer's expectation from the retained requirement, not observed.
"""

import json
import sys
from copy import deepcopy
from pathlib import Path

from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import canonical_json, content_hash, spec_hash
from uarch_contract.mapped import canonical_owners, hardware_projection, resolve_frequencies, TaskGraph

root, inputs, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
production = json.loads((inputs / "production.json").read_text())
TEST = {"checkpoint": "B", "invocation": "test", "eligibility": "verification_only"}


def rehash(raw, *, graph=False, point=False, hardware=False):
    b, p = raw["workload_closure"], raw["mapped_point"]
    if graph:
        p["task_graph"]["graph_hash"] = content_hash(p["task_graph"], exclude=("graph_hash",))
    if graph or point:
        p["payload_hash"] = content_hash(p, exclude=("payload_hash",))
        b["points"] = [p]
        raw["point_hash"] = p["payload_hash"]
        spec = HardwareSpec.model_validate(b["hardware_spec"])
        raw["freq_hz"] = resolve_frequencies(spec, p["frequency_ratio"]).model_dump(mode="json")
        raw["frequency_ratio"], raw["initial_state"] = p["frequency_ratio"], p["initial_state"]
        raw["priming_iterations"] = p["priming_iterations"]
    if hardware:
        spec = HardwareSpec.model_validate(b["hardware_spec"])
        b["hardware_spec_hash"] = raw["hardware_spec_hash"] = spec_hash(spec)
        raw["hardware"] = hardware_projection(spec).model_dump(mode="json")
        raw["owners"] = [o.model_dump(mode="json") for o in canonical_owners(
            spec, TaskGraph.model_validate(p["task_graph"]))]
        raw["freq_hz"] = resolve_frequencies(spec, p["frequency_ratio"]).model_dump(mode="json")
    b["bundle_hash"] = content_hash(b, exclude=("bundle_hash",))
    raw["bundle_hash"] = b["bundle_hash"]
    raw["job_hash"] = content_hash(raw, exclude=("job_hash",))
    return raw


def as_test(raw):
    raw["admission"] = dict(TEST)
    raw["workload_closure"]["admission"] = dict(TEST)
    return raw


manifest = []


def emit(name, data, *, python, native, test_only=False, note=""):
    payload = data if isinstance(data, bytes) else canonical_json(data).encode()
    (out / f"{name}.json").write_bytes(payload)
    manifest.append(dict(name=name, expect_python=python, expect_native=native,
                         test_only=test_only, note=note))


# Hardware eligibility: same component on altered (non-production) hardware.
hw = deepcopy(production)
hw["workload_closure"]["hardware_spec"]["cores"]["core_type"]["job_overhead_cycles"]["value"] = 16.0
emit("hw-altered-production", rehash(hw, hardware=True), python="UnsupportedHardware",
     native="UnsupportedHardware", note="job_overhead_cycles 32->16 under production")
emit("hw-altered-test", rehash(as_test(deepcopy(hw)), hardware=True), python="accept",
     native="accept", test_only=True, note="same hardware, explicit test-only path")

# Clock law: production requires ratio 1 / 1 GHz.
clk = deepcopy(production)
clk["mapped_point"]["frequency_ratio"] = 2.0
emit("clock-ratio-2", rehash(clk, point=True), python="UnsupportedFrequency",
     native="UnsupportedFrequency")

# Initial state / priming.
for state in ("steady", "fixture_resident"):
    st = deepcopy(production)
    st["mapped_point"]["initial_state"] = state
    emit(f"state-{state}", rehash(st, point=True), python="UnsupportedInitialState",
         native="UnsupportedInitialState")
pr = deepcopy(production)
pr["mapped_point"]["priming_iterations"] = 1
emit("priming-1", rehash(pr, point=True), python="UnsupportedInitialState",
     native="UnsupportedInitialState")

# Unsupported capabilities.
fp = deepcopy(production)
fp["precision"] = "fp8"
emit("precision-fp8", rehash(fp), python="ValidationError", native="InvalidCarrier")
fd = deepcopy(production)
fd["fidelity_detail"]["noc"] = 1
emit("fidelity-noc1", rehash(fd), python="ValidationError", native="InvalidCarrier")
pk = deepcopy(production)
pk["engine"]["package_version"] = "0.0.2"
emit("package-version-0.0.2", rehash(pk), python="ValidationError", native="InvalidCarrier")
mv = deepcopy(production)
mv["engine"]["model"]["version"] = "1"
emit("model-version-1", rehash(mv), python="ValidationError", native="InvalidCarrier")

# Resource capacity and lifetime.
cap = deepcopy(production)
slot = next(x for x in cap["mapped_point"]["task_graph"]["buffers"] if x["id"] == "slot1")
slot["size_bytes"] = 16 * 1024 * 1024
emit("sram-capacity", rehash(cap, graph=True), python="CapacityExceeded|SramCapacityExceeded",
     native="CapacityExceeded|SramCapacityExceeded")
alias = deepcopy(production)
sw = next(x for x in alias["mapped_point"]["task_graph"]["buffers"] if x["id"] == "sw")
sw["offset_bytes"] = 0  # overlaps live sx; both consumed by c
emit("live-alias", rehash(alias, graph=True), python="LiveBufferAlias", native="LiveBufferAlias")
dep = deepcopy(production)
dep["mapped_point"]["task_graph"]["dependencies"] = [
    d for d in dep["mapped_point"]["task_graph"]["dependencies"] if d["before"] != "a"]
emit("dependency-dropped", rehash(dep, graph=True), python="InvalidDependency",
     native="InvalidDependency", note="compute c no longer waits for producer a of sx")

# Units / strict types.
un = deepcopy(production)
next(x for x in un["mapped_point"]["task_graph"]["buffers"] if x["id"] == "sx")["size_bytes"] = 30.5
emit("units-fractional-bytes", rehash(un, graph=True), python="ValidationError", native="InvalidCarrier")

# Scope: test transport fixture relabelled as production.
tr = json.loads((inputs / "test-synthetic-stage2-cc-v3.json").read_text())
prod_adm = {"checkpoint": "B", "invocation": "production", "eligibility": "component_only"}
tr["admission"] = dict(prod_adm)
tr["workload_closure"]["admission"] = dict(prod_adm)
emit("transport-as-production", rehash(tr), python="UnsupportedCheckpointScope|UnsupportedHardware",
     native="UnsupportedCheckpointScope|UnsupportedHardware|UnsupportedInitialState")

# Malformed / carrier.
emit("historical-v3", (root / "native/crates/uarch-engine/testdata/synthetic-stage2-cc-v3.json").read_bytes(),
     python="ValidationError", native="UnsupportedProtocol")
ex = deepcopy(production)
ex["trace"] = True
emit("unknown-field", rehash(ex), python="ValidationError", native="InvalidCarrier")
raw = canonical_json(production).encode()
emit("truncated", raw[: len(raw) // 2], python="ValueError", native="InvalidJson")
emit("noncanonical-whitespace", json.dumps(production, indent=1).encode(), python="ProtocolViolation",
     native="accept-or-refuse", note="Python requires canonical saved job; binary transport may parse")
emit("duplicate-key", raw[:-1] + b',"seed":0}', python="ValueError", native="InvalidJson")
st = deepcopy(production)
st["seed"] = 5  # no rehash
emit("hash-stale", st, python="ContentHashMismatch|ArtifactHashMismatch", native="ContentHashMismatch")

(out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
print(f"{len(manifest)} mutants written")
