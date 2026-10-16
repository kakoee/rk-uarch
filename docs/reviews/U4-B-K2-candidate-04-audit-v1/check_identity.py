# ruff: noqa: E401, E402, E731, I001, F401, E501
# Exact executed orchestration; preserve import order and origin-observation imports.
import sys, pathlib, json, hashlib, runpy

R = pathlib.Path(__file__).resolve().parent
S = R / "reference"
P = S / "docs/reviews/U4-A-K2-construction-v1"
C = P / "candidate-04"
sys.path[:0] = [str(S / "native/tools"), str(S / "src"), str(S / "contract"), str(S)]
reads = []


def audit(event, args):
    if event == "open" and isinstance(args[0], str):
        reads.append({"path": args[0], "mode": str(args[1]), "flags": args[2]})


sys.addaudithook(audit)
from generate_identity import generate

actual = generate(S, C / "BuildInputs.json", R / "regenerated")
expected = json.loads((C / "observations/identity.json").read_text())
assert actual == expected
p = actual["generated"]["path"]
assert (R / "regenerated" / p).read_bytes() == (R / "source" / p).read_bytes()
origins = {n: m.__file__ for n, m in sys.modules.copy().items() if getattr(m, "__file__", None)}
assert all(
    pathlib.Path(p).is_relative_to(S)
    for n, p in origins.items()
    if n.startswith(("rkuarch", "uarch_contract", "generate_identity"))
)
observed = list(reads)
sys.audit("u4.review.done")
report = {
    "identity": actual,
    "origins": origins,
    "observed_open_events": observed,
    "scope": "Python audit events from explicit generator import to return; does not observe interpreter startup, native DSO internals, stat calls or semantic environment use",
    "source_root": str(S),
}
(R / "output/generator-audit.json").write_text(json.dumps(report, indent=2) + "\n")
runpy.run_path(str(P / "check_handoff.py"), run_name="__main__")
print("Independent regenerated identity byte match; project origins private; handoff joins pass")
