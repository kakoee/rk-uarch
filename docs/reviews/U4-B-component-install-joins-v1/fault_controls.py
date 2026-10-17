"""Focused identity and O2 mutations in one private export; exact restoration always."""

import argparse
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("logs", type=Path)
    args = parser.parse_args()
    root = args.export.resolve()
    assert root.is_relative_to(Path("/tmp")) and not (root / ".git").exists()
    args.logs.mkdir(exist_ok=False)
    records = {}
    restorations = []

    def run(name: str, nodes: list[str], code: int) -> str:
        command = [
            sys.executable,
            "-I",
            "-B",
            str(PACKAGE / "isolated.py"),
            str(root),
            "pytest",
            "-q",
            *nodes,
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        output = result.stdout + result.stderr
        (args.logs / (name + ".log")).write_text(output)
        records[name] = dict(
            command=command, exit_code=result.returncode, sha256=sha(output.encode())
        )
        assert result.returncode == code, (name, output)
        assert "B-PRIVATE-ORIGINS " in output
        return output

    def experiment(path: str, detail: str, name: str, nodes: list[str], kills: bool) -> None:
        source = root / path
        original = source.read_bytes()
        lines = original.decode().splitlines(keepends=True)
        candidates = []
        for node in ast.walk(ast.parse(original)):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                call = node.value
                if isinstance(call.func, ast.Name) and call.func.id == "need" and call.args:
                    if isinstance(call.args[-1], ast.Constant) and call.args[-1].value == detail:
                        candidates.append(node)
            if isinstance(node, ast.Assert) and isinstance(node.msg, ast.Constant):
                if node.msg.value == detail:
                    candidates.append(node)
            if detail == "postimage equality" and isinstance(node, ast.Assert):
                if isinstance(node.msg, ast.JoinedStr):
                    candidates.append(node)
        assert len(candidates) == 1, (detail, candidates)
        node = candidates[0]
        assert node.end_lineno is not None
        mutant = "".join(
            lines[: node.lineno - 1] + [" " * node.col_offset + "pass\n"] + lines[node.end_lineno :]
        ).encode()
        try:
            source.write_bytes(mutant)
            output = run(name, nodes, 1)
            assert ("DID NOT RAISE" in output) == kills, (name, output)
            if not kills:
                assert "accumulator lifetime mechanism" in output
        finally:
            source.write_bytes(original)
            assert source.read_bytes() == original
        restored = run(name + "-restored", nodes, 0)
        assert "passed" in restored
        restorations.append(
            dict(
                source=path,
                guard=detail,
                original_sha256=sha(original),
                mutant_sha256=sha(mutant),
                restored_sha256=sha(source.read_bytes()),
                exact_restore=True,
                experiment=name,
                unsafe_behavioral_acceptance=(name == "O2-mechanism-only"),
                identity_discrimination=(name.startswith("CI-")),
                alternative_refusal=not kills,
            )
        )

    o2 = "validation/component/test_transient_lifetime.py"
    identity = "validation/component/test_installation_identity.py"
    checker = "validation/component/observations_v2.py"
    helper = "validation/component/installation_identity.py"
    run("O2-intact", [o2], 0)
    experiment(checker, "accumulator lifetime mechanism", "O2-mechanism-only", [o2], True)
    experiment(
        checker,
        "allocation access lifetime",
        "O2-access-only",
        [o2 + "::test_transient_free_at_first_final_consumer_is_too_early"],
        False,
    )
    experiment(
        helper,
        "installed K2 ADR prefix",
        "CI-K2-stream-only",
        [identity + "::test_adr_stream_tamper[K2-installed K2 ADR prefix]"],
        True,
    )
    experiment(
        helper,
        "reviewed component suffix",
        "CI-component-stream-only",
        [identity + "::test_adr_stream_tamper[component-reviewed component suffix]"],
        True,
    )
    experiment(
        helper,
        "postimage equality",
        "CI-postimage-only",
        [identity + "::test_f5_and_changed_identity_test_are_bound"],
        True,
    )
    (args.logs / "restoration.json").write_text(
        json.dumps(
            dict(
                scope=("O2 behavioral experiments and separate CI-C1 identity experiments; "
                       "never combine scores"),
                records=records,
                restorations=restorations,
                native_calls=0,
            ),
            indent=2,
        )
        + "\n"
    )
    print("O2 essential endpoint guard and early-free alternative refusal distinguished;")
    print("three CI identity guard experiments; all exact bytes restored and affected tests rerun.")


if __name__ == "__main__":
    main()
