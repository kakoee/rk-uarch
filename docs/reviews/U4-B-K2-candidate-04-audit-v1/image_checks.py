# ruff: noqa: E401, E402, E731, I001, F401, E501
# Exact executed orchestration; preserve import order and origin-observation imports.
import pathlib, importlib.util, json

R = pathlib.Path(__file__).resolve().parent
P = R / "reference/docs/reviews/U4-B-K2-construction-audit-v1"
s = importlib.util.spec_from_file_location("monitor", P / "trace_monitor.py")
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
c = m.run(
    R,
    "runtime-hashes",
    [
        "/usr/bin/sha256sum",
        "/lib/x86_64-linux-gnu/libc.so.6",
        "/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2",
        "/lib/x86_64-linux-gnu/libgcc_s.so.1",
        "/etc/ld.so.cache",
        "/usr/bin/readelf",
    ],
)
assert c["exit_code"] == 0 and not c["stop_reason"]
c = m.run(
    R, "metadata", [m.TOOL + "cargo", "metadata", "--locked", "--offline", "--format-version", "1"]
)
assert c["exit_code"] == 0 and not c["stop_reason"]
a = json.loads((R / "receipts/metadata/stdout").read_text())
b = json.loads(
    (R / "reference/docs/reviews/U4-A-K2-construction-v1/inputs/metadata-full.json").read_text()
)
assert a["resolve"] == b["resolve"]
assert a["workspace_members"] == b["workspace_members"]
print("runtime hashes recorded; actual full metadata graph equals A", len(a["packages"]))
