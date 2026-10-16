# ruff: noqa: E401, E402, E731, I001, F401, E501
# Exact executed orchestration; preserve import order and origin-observation imports.
import sys, pathlib, json, re, hashlib, collections

R = pathlib.Path(__file__).resolve().parent
S = R / "reference"
sys.path.insert(0, str(S / "docs/reviews/U4-B-K2-construction-audit-v1"))
from trace_canary import parse, CoverageError

build = json.loads(
    (S / "docs/reviews/U4-A-K2-construction-v1/candidate-04/BuildInputs.json").read_text()
)
declared = {f["path"]: f["byte_hash"] for f in build["source_files"]}
declared.update(
    {
        p: "sha256:" + hashlib.sha256((R / "source" / p).read_bytes()).hexdigest()
        for p in build["generated_identity_output_paths"]
    }
)
reports = {}
for mode in ["debug", "release"]:
    logs = {
        int(p.name.rsplit(".", 1)[1]): p.read_text()
        for p in (R / "receipts" / mode).glob(mode + ".trace.*")
    }
    events, children, roots = parse(logs)
    incoming = {}
    by_pid = collections.defaultdict(list)
    for e in events:
        by_pid[e["pid"]].append(e)
        if e["call"] in {"clone", "clone3", "fork", "vfork"} and re.match(
            r"^[1-9][0-9]*$", e["result"]
        ):
            incoming[int(e["result"])] = e
    changes = []
    for e in events:
        if e["call"] in {"chdir", "fchdir"} and e["result"] == "0":
            parent = incoming.get(e["pid"])
            assert parent is None or "CLONE_FS" not in parent["args"]
            assert not any(
                x["ordinal"] < e["ordinal"]
                and x["call"] in {"clone", "clone3", "fork", "vfork"}
                and re.match(r"^[1-9][0-9]*$", x["result"])
                for x in by_pid[e["pid"]]
            )
            changes.append({"pid": e["pid"], "ordinal": e["ordinal"], "path": e["args"]})
    assert not any(
        "/diagnostics" in e["args"] for e in events if e["call"] in {"execve", "execveat"}
    )
    j = json.loads((R / "output" / f"{mode}-read-audit-v2.json").read_text())
    assert not j["unresolved_fd_records"]
    assert not j["diagnostic_child_exec_mentions"]
    actual = {}
    for p, v in j["paths"].items():
        if p.startswith("/work/") and v["read_or_mapping_count"]:
            f = R / "source" / p[6:]
            if f.is_file():
                h = "sha256:" + hashlib.sha256(f.read_bytes()).hexdigest()
                assert declared.get(p[6:]) == h, (p, h)
                actual[p[6:]] = h
    controls = []
    for fault in ["missing-child", "missing-terminal"]:
        altered = dict(logs)
        if fault == "missing-child":
            del altered[min(children)]
        else:
            altered[min(logs)] = (
                "\n".join(
                    line
                    for line in altered[min(logs)].splitlines()
                    if "+++ exited" not in line and "+++ killed" not in line
                )
                + "\n"
            )
        try:
            parse(altered)
        except CoverageError as err:
            controls.append({"fault": fault, "refusal": str(err)})
        else:
            raise AssertionError(fault)
    parse(logs)
    reports[mode] = {
        "processes": len(logs),
        "records": len(events),
        "all_child_and_terminal_records": True,
        "cwd_changes": changes,
        "cwd_sharing_concern": "all changes occur in private FS descendants before their children",
        "source_files_observed": actual,
        "negative_controls": controls,
        "original_restored_pass": True,
        "diagnostic_environment_or_child_path_leak": False,
        "unresolved_fd_records": 0,
        "path_classes": j["path_classes"],
    }
(R / "output/trace-interpretation.json").write_text(json.dumps(reports, indent=2) + "\n")
print(
    {
        m: {
            "processes": r["processes"],
            "records": r["records"],
            "actual_source_files": len(r["source_files_observed"]),
            "cwd_changes": len(r["cwd_changes"]),
        }
        for m, r in reports.items()
    }
)
