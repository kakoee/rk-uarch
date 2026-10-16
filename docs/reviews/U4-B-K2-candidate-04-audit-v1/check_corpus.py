# ruff: noqa: E401, E402, E731, I001, F401, E501
# Exact executed orchestration; preserve import order and origin-observation imports.
import sys, pathlib, json, hashlib, importlib.util, collections

R = pathlib.Path(__file__).resolve().parent
S = R / "reference"
P = S / "docs/reviews/U4-A-K2-construction-v1"
B = S / "docs/reviews/U4-B-K2-construction-audit-v1"
sys.path[:0] = [str(S / "src"), str(S / "contract"), str(B)]
from uarch_contract.hashing import canonical_json, content_hash
from uarch_contract.mapped import NativeEngineIdentity
from first_use_checks import fixture_job

frozen = json.loads((B / "first-use-candidate.json").read_text())
corpus = P / "corpus"
inventory = json.loads((corpus / "inventory.json").read_text())
expected = json.loads((corpus / "expectations.json").read_text())
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for p, v in frozen["files"].items():
    assert h(corpus / p) == v, (p, v)
assert {r["case_id"] for r in inventory["cases"]} == set(frozen["cases"]) == set(expected)
identity = json.loads((P / "candidate-04/observations/identity.json").read_text())
engine = NativeEngineIdentity.model_validate(identity["engine"])
actualjobs = json.loads((P / "candidate-04/jobs-inventory.json").read_text())["jobs"]
actualbyhash = {r["job_hash"]: r for r in actualjobs}
seen = []
for row in inventory["cases"]:
    case = row["case_id"]
    assert row["clock_setup"] == expected[case]["clock_setup"]
    assert row["execution_outcome"] == expected[case]["outcome"]
    actual = fixture_job(S, corpus, case, engine)
    got = (R / actualbyhash[actual["job_hash"]]["file"]["path"]).read_bytes()
    assert got == canonical_json(actual).encode()
    seen.append(actual["job_hash"])
assert len(seen) == len(set(seen)) == 133
out = R / "dto-regenerated"
out.mkdir()
dtos = {}
for name, file, receipt in [
    ("dto_vectors", "b-dto.json", "dto-freeze.json"),
    ("dto_key_vectors", "b-keys.json", "dto-key-freeze.json"),
    ("dto_coordinate_vectors", "b-coordinates.json", "dto-coordinate-freeze.json"),
]:
    s = importlib.util.spec_from_file_location(name, B / (name + ".py"))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    got = m.prepare(S, out / file)
    assert got == json.loads((B / receipt).read_text())
    assert (out / file).read_bytes() == (R / "vectors/peer-dto" / file).read_bytes()
    dtos[name] = got
report = {
    "corpus_file_hashes_equal_B_freeze": len(frozen["files"]),
    "complete_actual_jobs_equal_independent_B_assembly": 133,
    "original_ids": len(frozen["original_ids"]),
    "added_ids": len(frozen["added_ids"]),
    "K07": sum(k.startswith("K07-") for k in expected),
    "outcomes": dict(collections.Counter(r["outcome"] for r in expected.values())),
    "profile_hash": frozen["profile_hash"],
    "registry_hash": frozen["registry_hash"],
    "dtype_freezes": dtos,
    "engine": identity["engine"],
    "public_mapped_executions": 0,
}
(R / "output/corpus-audit.json").write_text(json.dumps(report, indent=2) + "\n")
print("133 exact actual jobs and corpus bindings; 48 Python DTO expectations rederived unchanged")
