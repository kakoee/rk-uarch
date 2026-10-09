"""Keep the old strict support refusal operative; no input or artifact rebinding."""
import hashlib
import json
from pathlib import Path

from scripts.u2_inputs import load_inputs, support_files

ROOT = Path.cwd()
OUT = ROOT / "docs/reviews/U2-A-RR-C1"
ADOPTED = ROOT / "contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963"
INPUTS = ADOPTED / "u2-inputs"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


support = json.loads((INPUTS / "support-files.json").read_text())
assert len(support) == 84
assert set(support) == {p.relative_to(ROOT).as_posix() for p in support_files()}
changed = {
    name: {"accepted": value, "current": digest(ROOT / name)}
    for name, value in support.items() if digest(ROOT / name) != value
}
assert changed == {"src/rkuarch/table/build.py": {
    "accepted": "ece53ed1bcb1ca02fdcc450ff4b1ee99da321f699fadcb5b446ea07f17fe4acc",
    "current": "c91880cb7ca8977e6ecf491109a8459394af39c6efab82714d34c8cdd895f9e6",
}}
manifest = "81df43c063396c89bd3333f43957c71efc7087cfa65b2a401177f2227fca8898"
assert digest(INPUTS / "SHA256SUMS") == manifest
try:
    load_inputs(INPUTS, manifest, check_support=True)
except ValueError as exc:
    refusal = str(exc)
    assert refusal == "input support changed: src/rkuarch/table/build.py", refusal
else:
    raise AssertionError("old support incorrectly accepted")
result = dict(expected_strict_refusal=refusal, check_support=True, support_count=84,
              unchanged_support_count=83, changed_support=changed,
              accepted_input_manifest_sha256=manifest,
              support_inventory_sha256=digest(INPUTS / "support-files.json"),
              adopted_manifest_sha256=digest(ADOPTED / "MANIFEST.json"),
              input_files_validated_before_support_refusal=True,
              authority="Implementation only; historical adoption unchanged. U0002 two human runs and separate explicit adoption remain required.")
(OUT / "support-lifecycle.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
