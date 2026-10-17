"""Current candidate deltas, protected postimages and selected-support closure."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from uarch_contract.hashing import content_hash

from scripts import u2_support

ROOT = Path(__file__).resolve().parents[3]
HUMAN = "3949b104d0eaae95a7452f976c2afa048fa82ff1"
CANDIDATE = "53ea633993a77b1f9d54698c6e8fb06aa123bd81"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--candidate", default=CANDIDATE)
    args = parser.parse_args()
    candidate = args.candidate
    install = json.loads(
        (ROOT / "docs/reviews/U4-B-component-install-joins-v1/postimages.json").read_text()
    )
    for row in install["paths"]:
        assert sha(git("show", HUMAN + ":" + row["path"])) == row["postimage_sha256"]
        assert sha((ROOT / row["path"]).read_bytes()) == row["postimage_sha256"]
    selected = u2_support.inventory(root=ROOT)
    changed = [p for p, h in selected.items() if sha(git("show", HUMAN + ":" + p)) != h]
    assert not changed
    for prefix in ("src/rkuarch/engines/native", "docs/reviews/U4-K2-campaign-throughput-v1"):
        assert not git("diff", HUMAN, "HEAD", "--", prefix)
    assert not git("diff", candidate, "HEAD", "--", "native")
    deltas = []
    before_paths = set(git("ls-tree", "-r", "--name-only", HUMAN, "native").decode().splitlines())
    for path in git("diff", "--name-only", HUMAN, candidate, "--", "native").decode().splitlines():
        before = sha(git("show", HUMAN + ":" + path)) if path in before_paths else None
        after = sha(git("show", candidate + ":" + path))
        assert sha((ROOT / path).read_bytes()) == after
        deltas.append(dict(path=path, preimage_sha256=before, postimage_sha256=after))
    freeze_path = ROOT / "docs/reviews/U4-B-component-native-v1/preparation-freeze.json"
    freeze = json.loads(freeze_path.read_text())
    # The existing freeze declares its exact manifest shape; retain it as an opaque identity too.
    input_freeze = json.loads(
        (ROOT / "docs/reviews/U4-B-component-native-v1/input-freeze-v2.json").read_text()
    )
    for p, h in input_freeze["sources"].items():
        assert sha((ROOT / p).read_bytes()) == h
    history = ROOT / "docs/reviews/U4-B-component-stage2-v1/execution-selection.json"
    assert sha(history.read_bytes()) == input_freeze["historical_selection_sha256"]
    import uarch_contract.mapped as mapped

    import validation.component.observations_v2 as checker

    report = dict(
        source_commit=candidate,
        human_install_commit=HUMAN,
        installed_postimages_verified=len(install["paths"]),
        native_deltas=deltas,
        selected_support=selected,
        selected_support_hash=content_hash(selected),
        selected_support_changed=changed,
        U0002_generation_required=False,
        protected_installation_permission=False,
        K2_runner_and_campaign_unchanged=True,
        historical_selection_sha256=sha(history.read_bytes()),
        preparation_freeze_sha256=sha(freeze_path.read_bytes()),
        preparation_freeze=freeze,
        origins=dict(support=u2_support.__file__, mapped=mapped.__file__, checker=checker.__file__),
    )
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        len(deltas),
        "native deltas;",
        len(selected),
        "unchanged support files;",
        len(install["paths"]),
        "exact installed postimages",
    )


if __name__ == "__main__":
    main()
