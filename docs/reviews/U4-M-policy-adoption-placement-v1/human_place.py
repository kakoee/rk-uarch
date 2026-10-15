"""Human placement of ten approved paths. --check is read-only; never generate/commit/push."""

import argparse
import contextlib
import hashlib
import io
import json
import os
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REVIEW = ROOT / "docs/reviews/U4-AD-M1-and-K1-reconciliation-v1"
PROPOSAL = "eb99399b96b1271a097aa9f635510f84622bf8dc"
OUTPUT = ROOT / "tables/U4-M-policy-adoption-v1"


def require(ok, message):
    if not ok:
        raise SystemExit("STOP: " + message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(path):
    require(not any(p.is_symlink() for p in (path, *path.parents)), "symlink: " + str(path))


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    require(result.returncode == 0, result.stderr.decode().strip() or "Git operation refused")
    return result.stdout


def pinned(path, commit):
    safe(path)
    require(
        path.read_bytes() == git(ROOT, "show", commit + ":" + path.relative_to(ROOT).as_posix()),
        "package drift: " + str(path),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--helper-commit", required=True)
    args = parser.parse_args()
    require(
        args.check or os.environ.get("UARCH_HUMAN") == "1", "human placement requires UARCH_HUMAN=1"
    )
    require(sys.flags.isolated and sys.dont_write_bytecode, "use reviewed Python -I -B")
    require(not sys.flags.optimize, "assertion-bearing saved audit requires non-optimized Python")
    for name in (
        "PYTHONPATH",
        "MYPYPATH",
        "VIRTUAL_ENV",
        "PARAMS",
        "SHA",
        "RK",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_COUNT",
    ):
        require(not os.environ.get(name), "unset " + name)
    pin = args.helper_commit
    require(
        len(pin) == 40 and all(c in "0123456789abcdef" for c in pin), "full helper pin required"
    )
    git(ROOT, "merge-base", "--is-ancestor", PROPOSAL, "HEAD")
    git(ROOT, "merge-base", "--is-ancestor", pin, "HEAD")
    for name in ("human_place.py", "acceptance.json", "README.md"):
        pinned(HERE / name, pin)
    for name in ("placement-plan.json", "audit_saved.py", "next-decision.md"):
        pinned(REVIEW / name, PROPOSAL)
    for relative in (
        "docs/reviews/U4-M-policy-artifact-adoption-v1/audit.json",
        "docs/reviews/U4-M-policy-artifact-adoption-v1/proposed-adoption-review.json.txt",
        "docs/reviews/U4-M-policy-freeze-generation-v1/preflight.py",
        "docs/reviews/U4-M-policy-freeze-generation-v1/freeze.json",
    ):
        pinned(ROOT / relative, PROPOSAL)
    plan = json.loads((REVIEW / "placement-plan.json").read_bytes())
    approval = json.loads((HERE / "acceptance.json").read_bytes())
    require(
        approval
        == {
            "decision": "U4-M-policy-artifact-adoption-v1",
            "status": "accepted; human placement pending",
            "authorizer": "Javid (@jjaffari)",
            "approval": "yes",
            "proposal_commit": PROPOSAL,
            "placement_plan_sha256": digest(REVIEW / "placement-plan.json"),
            "source_commit": plan["source_commit"],
            "candidate_manifest_sha256": plan["candidate_manifest_sha256"],
            "paths": 10,
            "commit_push_k1_k2_closure": False,
        },
        "exact approval binding mismatch",
    )
    pre = runpy.run_path(str(ROOT / "docs/reviews/U4-M-policy-freeze-generation-v1/preflight.py"))
    spec = pre["SPEC"]
    require(sys.prefix == spec["source_prefix"], "wrong interpreter environment")
    pre["source_guard"]()
    a = pre["SOURCE"]
    require(
        git(a, "remote", "get-url", "origin").decode().strip()
        == "https://github.com/kakoee/rk-uarch.git",
        "A origin mismatch",
    )
    safe(OUTPUT)
    require(not OUTPUT.exists(), "placement already attempted; preserve receipt and stop")
    require(not OUTPUT.is_relative_to(a), "receipt must be outside frozen source")
    require(git(ROOT, "check-ignore", str(OUTPUT / "probe")).strip(), "receipt must be ignored")
    candidate = Path(plan["candidate"])
    canonical = a / plan["canonical_destination"]
    for directory in (candidate, canonical, Path(spec["inputs"]), pre["OUTPUT"] / "receipts"):
        safe(directory)
        for path in directory.rglob("*"):
            safe(path)
    # Exact saved artifacts and immutable execution receipts, not a new oracle run.
    audit_module = runpy.run_path(str(REVIEW / "audit_saved.py"))
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        audit_module["main"]()
    audit = json.loads(buffer.getvalue())
    require(
        audit["candidate_manifest_sha256"] == plan["candidate_manifest_sha256"], "audit identity"
    )
    from scripts import vendor_rk as vendor
    from tests import u2_refresh

    require(Path(u2_refresh.__file__).resolve().is_relative_to(a), "consumer import origin")
    require(vendor.ROOT == a, "vendor import origin")
    files = {
        p.relative_to(candidate).as_posix(): p.read_bytes()
        for p in candidate.rglob("*")
        if p.is_file()
    }
    old_files = {
        p.relative_to(canonical).as_posix(): p.read_bytes()
        for p in canonical.rglob("*")
        if p.is_file()
    }
    require(len(files) == plan["complete_candidate_files"] == 49, "candidate file count")
    require(set(old_files) - set(files) == set(), "artifact removals are not approved")
    require(sorted(set(files) - set(old_files)) == plan["added_artifact_paths"], "added members")
    changed = sorted(n for n in old_files if old_files[n] != files[n])
    require(changed == plan["changed_artifact_paths"], "changed members")
    expected = {
        plan["canonical_destination"] + "/" + n: files[n]
        for n in changed + plan["added_artifact_paths"]
    }
    with tempfile.TemporaryDirectory(prefix="u4-human-placement-check-") as temp:
        scratch = Path(temp)
        for name, hashes in plan["binding_paths"].items():
            target = a / name
            safe(target)
            if hashes["before_sha256"] is None:
                require(not target.exists(), "new target already exists: " + name)
            else:
                require(digest(target) == hashes["before_sha256"], "target drift: " + name)
                copy = scratch / name
                copy.parent.mkdir(parents=True, exist_ok=True)
                copy.write_bytes(target.read_bytes())
        for patch in plan["patches"]:
            path = ROOT / patch["path"]
            pinned(path, PROPOSAL)
            require(digest(path) == patch["sha256"], "patch digest mismatch")
            subprocess.run(["git", "apply", "--unidiff-zero", str(path)], cwd=scratch, check=True)
        for name, hashes in plan["binding_paths"].items():
            require(digest(scratch / name) == hashes["after_sha256"], "postimage mismatch: " + name)
            expected[name] = (scratch / name).read_bytes()
    require(
        sorted(expected) == plan["expected_changed_paths"] and len(expected) == 10,
        "ten paths required",
    )
    require(
        hashlib.sha256(expected[plan["proposed_review_path"]]).hexdigest()
        == plan["proposed_review_file_sha256"],
        "administrative review bytes",
    )
    pre["source_guard"]()
    print(
        json.dumps(
            {
                "preflight": "passed",
                "paths": 10,
                "candidate_files": 49,
                "source_commit": plan["source_commit"],
                "placement_executed": False,
            }
        ),
        flush=True,
    )
    if args.check:
        print("Read-only check complete; no live adoption, staging, commit or push.")
        return
    # Human-only placement starts here. All preimages, postimages and authority checked above.
    OUTPUT.mkdir()
    (OUTPUT / "preflight.json").write_text(json.dumps(audit, indent=2) + "\n")
    for name, data in expected.items():
        target = a / name
        safe(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        temporary.chmod(0o644)
        os.replace(temporary, target)
    require(git(a, "rev-parse", "HEAD").decode().strip() == plan["source_commit"], "HEAD moved")
    require(not git(a, "diff", "--cached", "--name-only").strip(), "index changed")
    modified = set(git(a, "diff", "--name-only").decode().splitlines())
    new = set(git(a, "ls-files", "--others", "--exclude-standard").decode().splitlines())
    require(modified | new == set(expected), "unexpected live change scope")
    for name, data in expected.items():
        require((a / name).read_bytes() == data, "placed bytes mismatch: " + name)
    for name, data in files.items():
        require((canonical / name).read_bytes() == data, "complete candidate mismatch: " + name)
    vendor.check_manifest(canonical)
    vendor.check_snapshot_inputs(canonical, check_support=True)
    vendor.check_generator(canonical, current=True)
    review = u2_refresh.adoption_authority(
        canonical, a / plan["proposed_review_path"], plan["proposed_review_file_sha256"]
    )
    require(review.review_hash == plan["proposed_review_hash"], "adoption authority mismatch")
    receipt = {
        "decision": plan["decision"],
        "status": "human placement verified; unstaged and uncommitted",
        "helper_commit": pin,
        "source_commit": plan["source_commit"],
        "old_manifest_sha256": plan["old_manifest_sha256"],
        "candidate_manifest_sha256": plan["candidate_manifest_sha256"],
        "changed_paths": sorted(expected),
        "strict_currentness": True,
        "staged": False,
        "committed": False,
        "pushed": False,
        "generation_native_execution_k1_k2_closure": False,
    }
    with (OUTPUT / "placement.json").open("x") as stream:
        stream.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    print("STOP: return receipt for coordinator verification. Commit and push remain separate.")


if __name__ == "__main__":
    main()
