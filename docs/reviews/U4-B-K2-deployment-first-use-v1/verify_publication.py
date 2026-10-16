"""Future read-only publication verifier. Prints proposed placement bytes; never installs.

A coordinator must first record the genuine human reply and publish the actual
preflight, decision and HostRecord. This tool cannot authenticate a human itself.
"""

import argparse
import json
import subprocess
from pathlib import Path

from deployment import HERE, digest, publication_blob, require

PREFIX = "docs/reviews/U4-K2-first-use-authorization-v1/"
PACKAGE = "docs/reviews/U4-B-K2-deployment-first-use-v1/"
AUDIT = "docs/reviews/U4-B-K2-candidate-04-audit-v1/HostRecord-proposal.json"
AUDIT_COMMIT = "94b072ef5b78aab9a3c1ff97639ddfb4f65b9e26"


def verify(repo, package_commit, acceptance_commit, hashes):
    # Publication is independent of the in-container resolver's declarative commit field.
    for commit in [package_commit, acceptance_commit]:
        require(len(commit) == 40, "full published commit required")
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "refs/remotes/origin/main"],
            cwd=repo,
            check=True,
        )
    for path in sorted(HERE.iterdir()):
        if path.is_file() and path.suffix in (".py", ".json", ".md", ".txt"):
            publication_blob(repo, package_commit, PACKAGE + path.name, digest(path.read_bytes()))
    documents = {}
    for name in [
        "human-decision.json",
        "HostRecord.json",
        "deployment-approval.json",
        "preflight.json",
    ]:
        documents[name] = publication_blob(repo, acceptance_commit, PREFIX + name, hashes[name])
    plan = json.loads((HERE / "campaign-plan.json").read_bytes())
    decision = json.loads(documents["human-decision.json"])
    require(
        decision
        == {
            "format": "uarch-k2-human-first-use-decision/1",
            "accepted_by": "Javid (@jjaffari)",
            "reply": "yes",
            "subject": plan["subject"],
        },
        "exact genuine recorded engine decision required",
    )
    proposal = subprocess.check_output(["git", "show", AUDIT_COMMIT + ":" + AUDIT], cwd=repo)
    record = json.loads(proposal)["proposed_fields"]
    record["decision"] = {
        "path": PREFIX + "human-decision.json",
        "byte_hash": hashes["human-decision.json"],
    }
    require(
        json.loads(documents["HostRecord.json"]) == record,
        "HostRecord differs from reviewed fields",
    )
    runtime_hash = digest((HERE / "runtime.json").read_bytes())
    campaign_hash = digest((HERE / "campaign-files.expected.json").read_bytes())
    plan_hash = digest((HERE / "campaign-plan.json").read_bytes())
    approval = json.loads(documents["deployment-approval.json"])
    require(
        approval
        == {
            "format": "uarch-k2-deployment-approval/1",
            "accepted_by": "Javid (@jjaffari)",
            "reply": "yes",
            "package_commit": package_commit,
            "subject": plan["subject"],
            "runtime_hash": runtime_hash,
            "campaign_files_hash": campaign_hash,
            "plan_hash": plan_hash,
        },
        "exact recorded deployment permission required",
    )
    preflight = json.loads(documents["preflight.json"])
    require(
        preflight["status"] == "runtime-import-preflight-passed"
        and preflight["runtime_hash"] == runtime_hash
        and preflight["campaign_files_hash"] == campaign_hash
        and preflight["mapped_jobs_executed"] == 0
        and preflight["resolver_authority_installed"] is False,
        "actual matching preflight required",
    )
    selector = {
        "format": "uarch-k2-host-selector/1",
        "repository": "/candidate",
        "acceptance_commit": acceptance_commit,
        "record_path": PREFIX + "HostRecord.json",
        "record_byte_hash": hashes["HostRecord.json"],
    }
    release = {
        "status": "human-authorized-first-use",
        "subject": plan["subject"],
        "acceptance_commit": acceptance_commit,
        "record_byte_hash": hashes["HostRecord.json"],
        "package_commit": package_commit,
        "preflight_byte_hash": hashes["preflight.json"],
        "runtime_hash": runtime_hash,
        "campaign_files_hash": campaign_hash,
        "plan_hash": plan_hash,
        "deployment_approval": {
            "path": PREFIX + "deployment-approval.json",
            "byte_hash": hashes["deployment-approval.json"],
        },
    }
    return {"selector": selector, "runtime_release": release}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--package-commit", required=True)
    p.add_argument("--acceptance-commit", required=True)
    p.add_argument(
        "--hashes",
        type=Path,
        required=True,
        help="Independently checked four published blob hashes, no default placeholders",
    )
    args = p.parse_args()
    print(
        json.dumps(
            verify(
                args.repo,
                args.package_commit,
                args.acceptance_commit,
                json.loads(args.hashes.read_bytes()),
            ),
            sort_keys=True,
            indent=2,
        )
    )
