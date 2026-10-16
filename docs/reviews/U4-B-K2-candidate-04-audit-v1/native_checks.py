# ruff: noqa: E401, E402, E731, I001, F401, E501
# Exact executed orchestration; preserve import order and origin-observation imports.
import sys, pathlib, json, shutil, hashlib

R = pathlib.Path(__file__).resolve().parent
S = R / "reference"
P = S / "docs/reviews/U4-A-K2-construction-v1"
C = P / "candidate-04"
sys.path[:0] = [str(S / "native/tools"), str(S / "src"), str(S / "contract")]
import build_candidate as b
from check_refusals import check

assert pathlib.Path(b.__file__).is_relative_to(S)
(R / "workspace").symlink_to(R / "source", target_is_directory=True)
(R / "targets").mkdir()
(R / "commands").mkdir()
shutil.copyfile(C / "BuildInputs.json", R / "BuildInputs.json")
for mode in ["debug", "release"]:
    (R / "targets" / mode).symlink_to(R / (mode + "-target"), target_is_directory=True)
    expected = json.loads((C / f"BuildReceipt-{mode}.json").read_text())["executable"]["byte_hash"]
    (R / f"{mode}-binaries.json").write_text(json.dumps({"executable_byte_hash": expected}))
    for action in ["test", "peer", "validate"]:
        b.execute(R, action, mode)
    check(R, mode)
    assert b.digest(R / "targets" / mode / mode / "uarch-engine") == expected
    print(
        mode,
        "45 units, 48 frozen DTOs, 133 admissions, 11 actual public refusals passed",
        flush=True,
    )
