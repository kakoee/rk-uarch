"""Read-only approval, installation, selected-support and historical input audit."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from uarch_contract.hashing import content_hash

from scripts import u2_support

ROOT = Path(__file__).resolve().parents[3]
HUMAN = "3949b104d0eaae95a7452f976c2afa048fa82ff1"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_bytes(commit, path):
    return subprocess.check_output(["git", "show", commit + ":" + path], cwd=ROOT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    acceptance_path = "docs/reviews/U4-component-native-approved-v1/acceptance.json"
    acceptance = json.loads((ROOT / acceptance_path).read_bytes())
    assert acceptance["human_component_commit"] == HUMAN
    proposal = acceptance["proposal_commit"]
    for name, digest in acceptance["approved_document_hashes"].items():
        assert (
            sha(git_bytes(proposal, "docs/reviews/U4-component-native-development-v1/" + name))
            == digest
        )
    for name, digest in acceptance["released_prompt_hashes"].items():
        assert (
            sha((ROOT / "docs/reviews/U4-component-native-approved-v1" / name).read_bytes())
            == digest
        )
    installation = json.loads(
        (ROOT / "docs/reviews/U4-B-component-install-joins-v1/postimages.json").read_bytes()
    )
    for row in installation["paths"]:
        assert sha(git_bytes(HUMAN, row["path"])) == row["postimage_sha256"]
        assert sha((ROOT / row["path"]).read_bytes()) == row["postimage_sha256"]
    selected = u2_support.inventory(root=ROOT)
    changed = [path for path, digest in selected.items() if sha(git_bytes(HUMAN, path)) != digest]
    assert not changed, changed
    freeze = json.loads(
        (ROOT / "docs/reviews/U4-B-component-native-v1/input-freeze-v2.json").read_bytes()
    )
    assert freeze["selection_hash"] == content_hash(freeze, exclude=("selection_hash",))
    history = ROOT / "docs/reviews/U4-B-component-stage2-v1/execution-selection.json"
    assert sha(history.read_bytes()) == freeze["historical_selection_sha256"]
    for path, digest in freeze["sources"].items():
        assert sha((ROOT / path).read_bytes()) == digest
    for prefix in (
        "native",
        "src/rkuarch/engines/native",
        "docs/reviews/U4-K2-campaign-throughput-v1",
    ):
        subprocess.run(
            ["git", "diff", "--exit-code", HUMAN, "HEAD", "--", prefix],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
    report = dict(
        format="B-native-preparation-audit/1",
        source_parent_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        human_install_commit=HUMAN,
        installed_postimages_verified=len(installation["paths"]),
        acceptance_sha256=sha((ROOT / acceptance_path).read_bytes()),
        approval_documents_exact=True,
        historical_selection_sha256=freeze["historical_selection_sha256"],
        selected_support=selected,
        selected_support_hash=content_hash(selected),
        selected_support_changed_since_human_install=changed,
        native_source_unchanged_since_human_install=True,
        engine_runner_unchanged_since_human_install=True,
        U0002_generation_required_for_this_B_delta=False,
        protected_installation_permission_granted=False,
        origins=dict(u2_support=u2_support.__file__),
        scope="B preparation only; A candidate not published, final combined native audit pending",
    )
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        len(installation["paths"]),
        "installed postimages;",
        len(selected),
        "unchanged selected support files",
    )


if __name__ == "__main__":
    main()
