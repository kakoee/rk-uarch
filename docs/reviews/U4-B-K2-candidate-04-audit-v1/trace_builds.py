# ruff: noqa: E401, E402, E731, I001, F401, E501
# Exact executed orchestration; preserve import order and origin-observation imports.
import sys, pathlib, json, hashlib, importlib.util

R = pathlib.Path(__file__).resolve().parent
P = R / "reference/docs/reviews/U4-B-K2-construction-audit-v1"
s = importlib.util.spec_from_file_location("monitor", P / "trace_monitor.py")
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
assert json.loads((P / "canary-assessment.json").read_text())["accepted"]
# Preserve the reviewed monitor and security configuration. Only use A's exact
# permitted environment, keeping diagnostic loader search local to strace.
base = m.build_command
build = json.loads(
    (R / "reference/docs/reviews/U4-A-K2-construction-v1/candidate-04/BuildInputs.json").read_text()
)


def command(*a, **kw):
    name, argv = base(*a, **kw)
    i = argv.index("-i") + 1
    j = i
    while j < len(argv) and "=" in argv[j] and not argv[j].startswith("/"):
        j += 1
    argv[i:j] = [k + "=" + v for k, v in build["permitted_environment"].items()]
    return name, argv


m.build_command = command
results = {}
for config in build["mode_configs"]:
    mode = config["mode"]
    result = m.run(R, mode, [m.TOOL + "cargo", *config["cargo_args"]], trace=True, build=True)
    results[mode] = result
    if result["exit_code"] == 0 and not result["stop_reason"]:
        binary = R / (mode + "-target") / mode / "uarch-engine"
        actual = "sha256:" + hashlib.sha256(binary.read_bytes()).hexdigest()
        expected = json.loads(
            (
                R
                / f"reference/docs/reviews/U4-A-K2-construction-v1/candidate-04/BuildReceipt-{mode}.json"
            ).read_text()
        )["executable"]["byte_hash"]
        result["binary_byte_hash"] = actual
        result["equals_ordinary_binary"] = actual == expected
    (R / "output/trace-builds.json").write_text(json.dumps(results, indent=2) + "\n")
    print(
        mode,
        result["exit_code"],
        result["stop_reason"],
        result.get("equals_ordinary_binary"),
        result["elapsed_seconds"],
        flush=True,
    )
    assert (
        result["exit_code"] == 0 and not result["stop_reason"] and result["equals_ordinary_binary"]
    )
