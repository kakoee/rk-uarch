"""Private authority-free composition/fault test; never qualifies placement or runs native."""

import argparse
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

import publication

PACKAGE = "docs/reviews/U4-B-K2-combined-runtime-stage2-v1"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--subject", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    assert len(a.subject) == 40 and all(x in "0123456789abcdef" for x in a.subject)
    assert a.output.is_absolute() and a.output.is_relative_to("/tmp")
    assert not a.output.exists() and a.output.resolve() == a.output
    a.output.mkdir()
    raw = subprocess.check_output(
        ["/usr/bin/git", "--no-replace-objects", "archive", a.subject, PACKAGE],
        cwd=a.repo,
        env=publication.environment(a.output / "empty-home"),
    )
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        archive.extractall(a.output / "export", filter="data")
    sys.path.insert(0, str(a.output / "export" / PACKAGE))
    import bindings as b
    import launch
    import prepare

    data = (a.output / "export" / PACKAGE / "candidate.json").read_bytes()
    c = json.loads(data)

    def local_subject(repo, commit, name):
        # Test only: bind an actual immutable local commit, not a fictional published pin.
        # Production requires the actual remote; no authority files are made here.
        return subprocess.check_output(
            ["/usr/bin/git", "--no-replace-objects", "show", commit + ":" + name],
            cwd=repo,
            env=prepare.publication.environment(a.output / "empty-home"),
        )

    prepare.published = local_subject
    files = prepare.payload(a.repo, a.subject, c, data)
    root = a.output / "payload"
    for name, contents in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(contents)
    b.check_payload(root / "project", root / "helpers", root / "record", sealed=False)
    preview = a.output / "human-place.preview.sh"
    preview.write_bytes(b"#!/bin/sh\nexit 1\n" + prepare.script(files, True))
    subprocess.run(["sh", "-n", str(preview)], check=True)
    results = []

    def run(label, *, expected=None, program=None, overlay=None):
        output = a.output / label
        argv = launch.command("preflight", output, c)
        argv = [x.replace(str(b.NEW), str(root)) for x in argv]
        argv[-1] = argv[-1].replace('"preflight"', '"private-preflight"')
        if program is not None:
            argv[-1] = program
        if overlay is not None:
            src, dst = overlay
            i = argv.index("--entrypoint")
            argv[i:i] = ["--mount", f"type=bind,src={src},dst={dst},readonly"]
        failed = False
        try:
            launch.run(argv, "preflight", output, {"private_test": True, **b.identity(data)})
        except ValueError as error:
            b.need(
                str(error) == "incomplete launch; preserve all evidence", "expected outer failure"
            )
            failed = True
        stderr = (output / "preflight.stderr").read_text()
        receipt = b.read(output / "preflight-launch.json")
        if expected is None:
            b.need(not failed and receipt["exit_code"] == 0, "positive composition")
            pf = b.read(output / "preflight.json")
            b.need(
                pf["private_test"] and pf["status"] == "private-composition-passed",
                "non-authorizing receipt",
            )
            b.need(
                set(pf["origins"].values()) == {"/project/" + n for n in c["project"]}
                and pf["native_calls"] == 0
                and not pf["authority_resolved"],
                "actual origins / no authority",
            )
        else:
            b.need(failed and expected in stderr, "discriminating failure: " + label)
            b.need(not (output / "preflight.json").exists(), "failure before preflight/authority")
        results.append(
            {
                "control": label,
                "expected_failure": expected,
                "exit_code": receipt["exit_code"],
                "stderr_hash": b.digest(stderr.encode()),
                "launch_receipt_hash": b.digest((output / "preflight-launch.json").read_bytes()),
                "native_calls": 0,
            }
        )

    run("positive")
    target = root / "project/contract/uarch_contract/hardware.py"
    original = target.read_bytes()
    target.write_bytes(original + b"\n# private drift control\n")
    try:
        run("changed-closure", expected="payload bytes: contract/uarch_contract/hardware.py")
    finally:
        target.write_bytes(original)
    target.unlink()
    try:
        run("missing-closure", expected="exact payload membership")
    finally:
        target.write_bytes(original)
    extra = root / "project/extra.py"
    extra.write_bytes(b"# private extra member\n")
    try:
        run("extra-closure", expected="exact payload membership")
    finally:
        extra.unlink()
    helper = root / "helpers/parallel_entrypoint.py"
    original_helper = helper.read_bytes()
    helper.write_bytes(original_helper + b"\n# private helper drift\n")
    try:
        run("changed-helper", expected="payload bytes: parallel_entrypoint.py")
    finally:
        helper.write_bytes(original_helper)
    origin_program = (
        'import sys,types;sys.path.insert(0,"/combined");'
        'sys.modules["uarch_contract.foreign"]=types.SimpleNamespace('
        '__file__="/candidate/contract/uarch_contract/hardware.py");'
        'import runtime_entry;r=runtime_entry;r.main("private-preflight")'
    )
    run(
        "wrong-origin",
        expected="wrong project import origin: uarch_contract.foreign",
        program=origin_program,
    )
    name = "candidate/docs/reviews/U4-A-K2-construction-v1/candidate-04/BuildInputs.json"
    changed_build = a.output / "changed-BuildInputs.json"
    changed_build.write_bytes((b.OLD / name).read_bytes() + b"\n")
    run(
        "wrong-native-binding",
        expected="original native/runtime binding: " + name,
        overlay=(changed_build, "/" + name),
    )
    no_authority = (
        'import sys;sys.path.insert(0,"/combined");import runtime_entry as r;'
        "r.PRIVATE=True;r.release()"
    )
    run(
        "private-release-refusal",
        expected="private composition cannot authorize execution",
        program=no_authority,
    )
    # Successful imports/restoration again, including exact closure/helper rehash.
    b.check_payload(root / "project", root / "helpers", root / "record", sealed=False)
    for name, contents in files.items():
        b.need((root / name).read_bytes() == contents, "all original payload bytes restored")
    run("restored")
    (a.output / "checks.json").write_bytes(
        b.encoded(
            {
                "subject": a.subject,
                "subject_kind": "exact local commit; publication not asserted by this check",
                "candidate_hash": b.digest(data),
                "payload_files": {n: b.digest(v) for n, v in files.items()},
                "controls": results,
                "restored_exact_bytes": True,
                "project_files": 31,
                "native_calls": 0,
                "authority_installed": False,
                "private_only": True,
                "limitations": (
                    "Original immutable inputs checked; new files are UID1000 disposable readonly "
                    "mounts. Not actual root placement or real preflight. "
                    "No resolver session/native execution."
                ),
            }
        )
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
