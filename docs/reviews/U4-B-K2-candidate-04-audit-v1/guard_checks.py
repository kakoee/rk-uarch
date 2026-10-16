# ruff: noqa: E401, E402, E731, I001, F401, E501
# Exact executed orchestration; preserve import order and origin-observation imports.
import sys, pathlib, json, os, runpy

R = pathlib.Path(__file__).resolve().parent
S = R / "reference"
sys.path[:0] = [str(S), str(S / "src"), str(S / "contract")]
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
sys.argv = ["export_carriers.py", "--check"]
runpy.run_path(str(S / "native/tools/export_carriers.py"), run_name="__main__")
import pytest

prior = json.loads((S / "docs/reviews/U4-B-K2-construction-audit-v1/guard-checks.json").read_text())
args = [
    "-q",
    "-p",
    "no:cacheprovider",
    "-c",
    str(S / "pyproject.toml"),
    "--rootdir",
    str(S),
    str(S / "tests/unit/test_u2_support_policy.py"),
    "-k",
    " or ".join(prior["selection"]),
]
code = pytest.main(args)
assert code == 0
# Collection only: even an installed selector cannot launch a public job here.
code = pytest.main(
    [
        "--collect-only",
        "-q",
        "-p",
        "no:cacheprovider",
        "-c",
        str(S / "pyproject.toml"),
        "--rootdir",
        str(S),
        str(S / "tests/native/test_u4_a_k2_public.py"),
    ]
)
assert code == 0
print("schema export and 16 source/currentness guards pass; 266 public tests collected only")
