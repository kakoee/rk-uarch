"""Human-only approved artifact placement; --check is repository-read-only.

No oracle, staging, commit, test activation or push. Use A's Python with -I -B.
"""

import argparse
import hashlib
import json
import os
import runpy
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIMARY = HERE.parents[2]
PROPOSAL = PRIMARY / "docs/reviews/U3-artifact-adoption-v1"
APPROVED_PROPOSAL = "064473d21b6a0e42e965703e4ae2fbb09f7568ed"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def committed(path, commit):
    relative = path.relative_to(PRIMARY).as_posix()
    require(path.read_bytes() == git(PRIMARY, "show", commit + ":" + relative), relative + " drift")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--helper-commit")
    args = parser.parse_args()
    require(args.check or os.environ.get("UARCH_HUMAN") == "1", "human invocation required")
    require(args.check or args.helper_commit, "exact published helper commit required")
    if args.helper_commit:
        require(
            len(args.helper_commit) == 40
            and all(c in "0123456789abcdef" for c in args.helper_commit),
            "full helper commit required",
        )
        for name in ("human_place.py", "acceptance.json", "README.md"):
            committed(HERE / name, args.helper_commit)
    for name in (
        "placement-plan.json",
        "adoption-bindings.patch",
        "proposed-adoption-review.json.txt",
        "next-decision.md",
    ):
        committed(PROPOSAL / name, APPROVED_PROPOSAL)
    plan = json.loads((PROPOSAL / "placement-plan.json").read_bytes())
    approval = json.loads((HERE / "acceptance.json").read_bytes())
    require(
        approval["decision"] == "U3-artifact-adoption-v1"
        and approval["status"] == "accepted; human placement pending"
        and approval["proposal_commit"] == APPROVED_PROPOSAL,
        "exact adoption acceptance required",
    )
    for key in ("candidate_manifest_sha256", "binding_patch_sha256", "source_commit"):
        require(approval[key] == plan[key], "approval binding mismatch: " + key)
    freeze = runpy.run_path(
        str(PRIMARY / "docs/reviews/U3-combined-freeze-proposal-v1/preflight.py")
    )
    preflight = freeze["preflight"](
        proposal_commit="70adf0988b218aed895fcf5d2d8b039ca2ba0566", stage="during"
    )
    a, output = freeze["A"], freeze["OUTPUT"]
    require(preflight["source_commit"] == plan["source_commit"], "source binding")
    require(
        git(a, "remote", "get-url", "origin").decode().strip()
        == "https://github.com/kakoee/rk-uarch.git",
        "unexpected A origin",
    )
    for name in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply"):
        pending = git(a, "rev-parse", "--path-format=absolute", "--git-path", name)
        require(not Path(pending.decode().strip()).exists(), "unfinished Git operation")
    from scripts import vendor_rk as vendor
    from tests.u2_refresh import adoption_authority, audit_candidate

    candidate = output / "candidate"
    require(
        digest((candidate / "MANIFEST.json").read_bytes()) == plan["candidate_manifest_sha256"],
        "approved candidate manifest changed",
    )
    audit = audit_candidate(candidate)
    require(audit["rows"] == 1008 and audit["adopted"] is False, "candidate audit")
    canonical = a / plan["canonical_destination"]
    vendor.check_manifest(canonical)
    require(
        digest((canonical / "MANIFEST.json").read_bytes()) == plan["old_manifest_sha256"],
        "canonical predecessor changed",
    )
    files = {
        p.relative_to(candidate).as_posix(): p.read_bytes()
        for p in candidate.rglob("*")
        if p.is_file()
    }
    require(len(files) == plan["complete_candidate_files"] == 48, "complete candidate required")
    old_names = {p.relative_to(canonical).as_posix() for p in canonical.rglob("*") if p.is_file()}
    require(old_names == set(files), "unexpected artifact inventory change")
    changed = {name for name, data in files.items() if (canonical / name).read_bytes() != data}
    require(changed == set(plan["changed_artifact_paths"]), "unexpected artifact delta")
    patch = PROPOSAL / "adoption-bindings.patch"
    require(digest(patch.read_bytes()) == plan["binding_patch_sha256"], "patch changed")
    expected = {plan["canonical_destination"] + "/" + name: data for name, data in files.items()}
    with tempfile.TemporaryDirectory(prefix="u3-human-adoption-preflight-") as tmp:
        scratch = Path(tmp)
        for name, hashes in plan["binding_paths"].items():
            path = a / name
            freeze["safe"](path)
            if hashes["before_sha256"] is None:
                require(not path.exists(), "new target already exists: " + name)
            else:
                require(
                    digest(path.read_bytes()) == hashes["before_sha256"], "target drift: " + name
                )
                destination = scratch / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(path.read_bytes())
        subprocess.run(["git", "apply", "--unidiff-zero", str(patch)], cwd=scratch, check=True)
        for name, hashes in plan["binding_paths"].items():
            data = (scratch / name).read_bytes()
            require(digest(data) == hashes["after_sha256"], "proposed bytes mismatch: " + name)
            expected[name] = data
    review_name = "tests/fixtures/u3_rope/received-adoption-review.json"
    require(digest(expected[review_name]) == plan["proposed_review_file_sha256"], "review binding")
    expected_changed = {plan["canonical_destination"] + "/" + n for n in changed}
    expected_changed.update(plan["binding_paths"])
    require(len(expected_changed) == 7, "exact seven-path placement required")
    receipt_path = output / "receipts/adoption-placement.json"
    freeze["safe"](receipt_path)
    require(not receipt_path.exists(), "placement receipt already exists; do not rerun")
    print(json.dumps(dict(preflight="passed", paths=7, candidate_files=48), indent=2), flush=True)
    if args.check:
        print("Read-only preflight complete; no live placement, staging or commit.")
        return
    # Human-only mutation begins here, after complete content and scope verification.
    freeze["source_guard"]()
    for name, data in expected.items():
        destination = a / name
        freeze["safe"](destination)
        if destination.exists() and destination.read_bytes() == data:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        temporary.chmod(0o644)
        os.replace(temporary, destination)
    require(git(a, "rev-parse", "HEAD").decode().strip() == plan["source_commit"], "HEAD moved")
    require(not git(a, "diff", "--cached", "--name-only").strip(), "index changed")
    modified = set(git(a, "diff", "--name-only").decode().splitlines())
    untracked = set(git(a, "ls-files", "--others", "--exclude-standard").decode().splitlines())
    require(modified | untracked == expected_changed, "unexpected live change scope")
    for name, data in expected.items():
        require((a / name).read_bytes() == data, "placed bytes mismatch: " + name)
    vendor.check_manifest(canonical)
    vendor.check_generator(canonical, current=True)
    adoption_authority(canonical, a / review_name, plan["proposed_review_file_sha256"])
    receipt = dict(
        decision="U3-artifact-adoption-v1",
        status="human placement verified; unstaged and uncommitted",
        source_commit=plan["source_commit"],
        old_manifest_sha256=plan["old_manifest_sha256"],
        candidate_manifest_sha256=plan["candidate_manifest_sha256"],
        helper_commit=args.helper_commit,
        changed_paths=sorted(expected_changed),
        strict_currentness=True,
        staged=False,
        committed=False,
        protected_tests_activated=False,
        pushed=False,
    )
    with receipt_path.open("x") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    print("STOP: return this receipt. Test activation, staging, commit and push remain separate.")


if __name__ == "__main__":
    main()
