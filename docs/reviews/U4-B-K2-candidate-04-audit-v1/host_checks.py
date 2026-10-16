# ruff: noqa: E401, E402, E731, I001, F401, E501
# Exact executed orchestration; preserve import order and origin-observation imports.
import sys, pathlib, os, json

R = pathlib.Path(__file__).resolve().parent
S = R / "reference"
sys.path[:0] = [
    str(S),
    str(S / "src"),
    str(S / "contract"),
    str(S / "docs/reviews/U4-B-K2-construction-audit-v1"),
]
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
os.environ["B_K2_FIXTURES"] = "/tmp/u4-b-k2-readiness.zxo1dh65/fixtures"
import rkuarch.workload.mapped, uarch_contract.mapped, rkuarch.engines.native.host

origins = {
    n: m.__file__
    for n, m in sys.modules.copy().items()
    if n.startswith(("rkuarch", "uarch_contract")) and getattr(m, "__file__", None)
}
assert all(pathlib.Path(p).is_relative_to(S) for p in origins.values())
(R / "output/host-import-origins.json").write_text(json.dumps(origins, indent=2) + "\n")
import pytest

args = [
    "-q",
    "-p",
    "no:cacheprovider",
    "-c",
    str(S / "pyproject.toml"),
    "--rootdir",
    str(S),
    str(S / "tests/unit/test_u4_a_mapped_loader.py"),
    str(S / "tests/unit/test_u4_k2_process.py"),
    str(S / "tests/unit/test_u4_k2_host_paths.py"),
    str(S / "tests/unit/test_u4_k2_host_records.py"),
    str(S / "docs/reviews/U4-B-K2-construction-audit-v1/test_first_use.py"),
]
print("ARGS", json.dumps(args), flush=True)
raise SystemExit(pytest.main(args))
