"""Bounded known-record inventory with an explicit gap ledger; never strict coverage."""

import argparse
import ast
import collections
import hashlib
import json
import pathlib
import posixpath
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
RECIPE = ROOT / "docs/reviews/U4-B-K2-construction-audit-v1/read_trace_inventory.py"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def scan(logs):
    events, children, gaps, terminals = [], set(), [], set()
    for pid, text in logs.items():
        pending = None
        for ordinal, raw in enumerate(text.splitlines()):
            body = re.sub(r"^\d+\.\d+\s+", "", raw)
            loc = dict(pid=pid, ordinal=ordinal, raw=raw)
            if body.startswith(("+++ exited with ", "+++ killed by ")):
                terminals.add(pid)
                continue
            if body.startswith("--- "):
                continue
            if "<unfinished ...>" in body:
                if pending:
                    gaps.append(dict(**pending[1], reason="overlapping unfinished call"))
                pending = (body.split("<unfinished ...>")[0], loc)
                continue
            if body.startswith("<... "):
                if pending is None:
                    gaps.append(dict(**loc, reason="resumed call without beginning"))
                    continue
                body = pending[0] + body.split(" resumed>", 1)[1]
                pending = None
            match = re.fullmatch(r"([a-zA-Z_][a-zA-Z_0-9]*)\((.*)\)\s+=\s+(.*)", body)
            if not match:
                gaps.append(dict(**loc, reason="unparsed record; syscall identity unknown"))
                continue
            call, args, result = match.groups()
            if call in {
                "execve",
                "execveat",
                "open",
                "openat",
                "openat2",
                "readlink",
                "readlinkat",
                "chdir",
            } and re.search(r'"(?:\\.|[^"\\])*"\.\.\.', args):
                gaps.append(dict(**loc, reason="truncated relevant path/argv"))
            events.append(dict(pid=pid, ordinal=ordinal, call=call, args=args, result=result))
            if call in {"clone", "clone3", "fork", "vfork"}:
                child = re.match(r"([1-9][0-9]*)\b", result)
                if child:
                    children.add(int(child.group(1)))
        if pending:
            gaps.append(dict(**pending[1], reason="unfinished call at terminal/end"))
        if pid not in terminals:
            gaps.append(dict(pid=pid, reason="no terminal record"))
    roots = set(logs) - children
    assert not children - set(logs) and len(roots) == 1
    return events, children, roots, gaps, terminals


def projection_nodes():
    """Reuse the approved path classifier/walker, excluding parser and all writes."""
    tree = ast.parse(RECIPE.read_text())
    setup = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "classify":
            setup.append(node)
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id in {"quoted", "filecalls", "readcalls"}
            for t in node.targets
        ):
            setup.append(node)
    loop = next(n for n in tree.body if isinstance(n, ast.For))
    start = next(
        i
        for i, n in enumerate(loop.body)
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "by_pid" for t in n.targets)
    )
    end = next(
        i
        for i, n in enumerate(loop.body)
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "report" for t in n.targets)
    )
    return ast.Module(body=setup + loop.body[start : end + 1], type_ignores=[])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("build", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(pathlib.Path("/tmp"))
    out.mkdir(exist_ok=False)
    build = json.loads((args.build / "build.json").read_text())
    assert build["source_commit"] == "64837bea3724919facbc27be1c7f5644a6354cfa"
    reports = []
    for mode in ("debug", "release"):
        traces = sorted((args.build / "receipts" / mode).glob(mode + ".trace.*"))
        # Recheck every raw trace against the original bounded construction receipt.
        for path in traces:
            assert sha(path.read_bytes()) == build["commands"][mode]["files"][path.name]["sha256"]
        logs = {int(p.suffix[1:]): p.read_text() for p in traces}
        events, children, roots, gaps, terminals = scan(logs)
        namespace = dict(
            ast=ast,
            collections=collections,
            hashlib=hashlib,
            posixpath=posixpath,
            re=re,
            R=args.build.resolve(),
            mode=mode,
            events=events,
            children=children,
            roots=roots,
            logs=logs,
        )
        exec(
            compile(projection_nodes(), str(RECIPE) + " [known-record projection]", "exec"),
            namespace,
        )
        report = namespace["report"]
        report.update(
            strict_coverage_accepted=False,
            gaps=gaps,
            all_terminal_records_present=set(logs) == terminals,
            bounded_scope=(
                "parseable records only; unknown calls and unfinished outcomes remain gaps"
            ),
            classifier_recipe_sha256=sha(RECIPE.read_bytes()),
            raw_trace_hashes={p.name: sha(p.read_bytes()) for p in traces},
        )
        payload = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
        (out / (mode + ".json")).write_bytes(payload)
        summary = {
            k: v
            for k, v in report.items()
            if k not in {"paths", "raw_trace_hashes", "unresolved_fd_records"}
        }
        summary.update(
            inventory_sha256=sha(payload),
            unresolved_fd_records=len(report["unresolved_fd_records"]),
            raw_trace_count=len(traces),
        )
        reports.append(summary)
        print(mode, report["path_classes"], "gaps", len(gaps), flush=True)
    (out / "checks.json").write_text(
        json.dumps(
            dict(
                source_commit=build["source_commit"],
                build_receipt_sha256=sha((args.build / "build.json").read_bytes()),
                recipe_sha256=sha(pathlib.Path(__file__).read_bytes()),
                reports=reports,
                strict_coverage_accepted=False,
                raw_logs_modified=False,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
